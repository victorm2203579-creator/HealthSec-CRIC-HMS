"""
audit/views.py
==============
Views for audit log viewing, integrity checking, and reporting.

All views require COMPLIANCE or ADMIN role. Audit logs are read-only.
"""

import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog, AuditLogIntegrityCheck
from .services import AuditService
from .serializers import AuditLogSerializer

try:
    from core.export_service import ExportService
except ImportError:
    ExportService = None


def _check_audit_permission(user):
    """Check if user has permission to view audit logs."""
    return user.is_admin or user.is_compliance_officer


@login_required
def audit_log_list(request):
    """
    List all audit log entries with filtering and search.

    Filters: user, action_category, status, date range
    Search: description, target_model
    """
    if not _check_audit_permission(request.user):
        messages.error(request, 'You do not have permission to view audit logs.')
        return redirect('dashboard:index')

    # Get filters from query parameters
    user_filter = request.GET.get('user', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    days_filter = request.GET.get('days', '30')
    search_query = request.GET.get('q', '')

    # Base queryset
    qs = AuditLog.objects.select_related('user').order_by('-timestamp')

    # Apply filters
    if user_filter:
        qs = qs.filter(user__username__icontains=user_filter)

    if category_filter:
        qs = qs.filter(action_category=category_filter)

    if status_filter:
        qs = qs.filter(status=status_filter)

    if days_filter and days_filter.isdigit():
        cutoff = timezone.now() - timedelta(days=int(days_filter))
        qs = qs.filter(timestamp__gte=cutoff)

    if search_query:
        qs = qs.filter(
            Q(description__icontains=search_query) |
            Q(target_model__icontains=search_query) |
            Q(action__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(qs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Export option
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        response.write(AuditService.export_logs(qs, format='csv'))
        return response

    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'category_choices': AuditLog.ActionCategory.choices,
        'status_choices': AuditLog.Status.choices,
        'user_filter': user_filter,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'days_filter': days_filter,
        'search_query': search_query,
        'total_count': paginator.count,
    }

    return render(request, 'audit/log_list.html', context)


@login_required
def audit_log_detail(request, log_id):
    """
    Display detailed information for a single audit log entry.

    Shows all fields including old/new values and checksum integrity status.
    """
    if not _check_audit_permission(request.user):
        messages.error(request, 'You do not have permission to view audit logs.')
        return redirect('dashboard:index')

    log = get_object_or_404(AuditLog, log_id=log_id)

    # Check integrity
    integrity_valid = AuditService.verify_integrity(log)

    context = {
        'log': log,
        'integrity_valid': integrity_valid,
    }

    return render(request, 'audit/log_detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def integrity_check(request):
    """
    Run and display audit log integrity check results.

    POST: Trigger a new integrity check
    GET: Display latest check results
    """
    if not _check_audit_permission(request.user):
        messages.error(request, 'You do not have permission to view audit logs.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        # Run integrity check
        result = AuditService.run_integrity_check(request.user)
        messages.info(
            request,
            f'Integrity check completed: {result["total_logs"]} logs checked, '
            f'{result["corrupted_logs"]} issues found.'
        )
        return redirect('audit:integrity_check')

    # Get latest check results
    latest_check = AuditLogIntegrityCheck.objects.first()
    all_checks = AuditLogIntegrityCheck.objects.all()[:20]

    # Get corrupted logs if available
    corrupted_logs = []
    if latest_check and latest_check.result == AuditLogIntegrityCheck.Result.TAMPERED:
        for log in AuditLog.objects.all():
            if not AuditService.verify_integrity(log):
                corrupted_logs.append(log)

    verified_logs = 0
    if latest_check:
        verified_logs = latest_check.total_logs_checked - latest_check.corrupted_logs

    context = {
        'latest_check': latest_check,
        'all_checks': all_checks,
        'corrupted_logs': corrupted_logs,
        'verified_logs': verified_logs,
    }

    return render(request, 'audit/integrity_check.html', context)


@login_required
def audit_report(request):
    """
    Display audit statistics and reporting dashboard.

    Statistics: logs by category, by user, by status
    Charts: activity trends, most active users
    """
    if not _check_audit_permission(request.user):
        messages.error(request, 'You do not have permission to view audit logs.')
        return redirect('dashboard:index')

    # Get time range from query param
    days = request.GET.get('days', '30')
    try:
        days = int(days)
    except ValueError:
        days = 30

    # Get statistics
    stats = AuditService.get_statistics(days=days)

    # Get daily activity data for chart
    from django.db.models import Count
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=days)
    daily_activity = (
        AuditLog.objects
        .filter(timestamp__gte=cutoff)
        .extra(select={'day': 'DATE(timestamp)'})
        .values('day')
        .annotate(count=Count('log_id'))
        .order_by('day')
    )

    context = {
        'stats': stats,
        'daily_activity': list(daily_activity),
        'days': days,
        'total_logs': AuditLog.objects.count(),
    }

    return render(request, 'audit/audit_report.html', context)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    REST API for audit logs.

    Provides read-only access to audit logs for other modules.
    Authentication required; COMPLIANCE/ADMIN role required.
    """

    queryset = AuditLog.objects.select_related('user').order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['action_category', 'status', 'user', 'target_model']
    search_fields = ['action', 'description', 'target_model']
    ordering_fields = ['timestamp', 'action_category', 'status']

    def get_queryset(self):
        """Restrict to compliance/admin users."""
        user = self.request.user
        if not (user.is_admin or user.is_compliance_officer):
            return AuditLog.objects.none()
        return super().get_queryset()

    @action(detail=False, methods=['post'])
    def create_log(self, request):
        """
        Create a new audit log entry from an internal API call.

        POST data:
        {
            "action_category": "ALERT",
            "action": "alert_created",
            "description": "Alert created for system X",
            "target_model": "Alert",
            "target_id": "uuid-here",
            "old_value": null,
            "new_value": {...}
        }
        """
        if not (request.user.is_admin or request.user.is_compliance_officer):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            log = AuditService.log(
                user=request.user,
                action_category=request.data.get('action_category', AuditLog.ActionCategory.SYSTEM),
                action=request.data.get('action', ''),
                description=request.data.get('description', ''),
                target_model=request.data.get('target_model', ''),
                target_id=request.data.get('target_id', ''),
                old_value=request.data.get('old_value'),
                new_value=request.data.get('new_value'),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_key=request.session.session_key if request.session else '',
                status=request.data.get('status', AuditLog.Status.SUCCESS),
            )

            return Response(
                AuditLogSerializer(log).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def verify_integrity(self, request, pk=None):
        """Verify integrity of a specific audit log entry."""
        log = self.get_object()
        is_valid = AuditService.verify_integrity(log)

        return Response({
            'log_id': str(log.log_id),
            'integrity_valid': is_valid,
            'checksum_stored': log.checksum,
        })

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


@login_required
def export_audit_logs(request):
    """Export audit logs in CSV, Excel, or PDF format."""
    if not (request.user.is_admin or request.user.is_compliance_officer):
        messages.error(request, 'You do not have permission to export audit logs.')
        return redirect('dashboard:index')

    if not ExportService:
        messages.error(request, 'Export service not available.')
        return redirect('audit:log')

    # Get filters from query parameters (same as audit_log_list)
    user_filter = request.GET.get('user', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    days_filter = request.GET.get('days', '30')
    search_query = request.GET.get('q', '')
    export_format = request.GET.get('format', 'csv').lower()

    # Build queryset with filters
    qs = AuditLog.objects.select_related('user').order_by('-timestamp')

    if user_filter:
        qs = qs.filter(user__username__icontains=user_filter)
    if category_filter:
        qs = qs.filter(action_category=category_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if days_filter and days_filter.isdigit():
        cutoff = timezone.now() - timedelta(days=int(days_filter))
        qs = qs.filter(timestamp__gte=cutoff)
    if search_query:
        qs = qs.filter(
            Q(description__icontains=search_query) |
            Q(target_model__icontains=search_query) |
            Q(action__icontains=search_query)
        )

    # Convert to list of dicts for export
    data = list(qs.values(
        'log_id', 'user__username', 'action_category', 'action',
        'description', 'timestamp', 'status', 'target_model', 'target_id'
    ))

    # Rename fields for display
    for record in data:
        record['User'] = record.pop('user__username', '')
        record['Category'] = record.pop('action_category', '')
        record['Action'] = record.pop('action', '')
        record['Description'] = record.pop('description', '')
        record['Timestamp'] = record.pop('timestamp', '')
        record['Status'] = record.pop('status', '')
        record['Target'] = record.pop('target_model', '')
        record['Target ID'] = record.pop('target_id', '')
        record.pop('log_id', None)

    headers = ['User', 'Category', 'Action', 'Description', 'Timestamp', 'Status', 'Target', 'Target ID']

    try:
        if export_format == 'csv':
            return ExportService.export_to_csv(data, 'audit_logs.csv', headers)
        elif export_format == 'excel':
            return ExportService.export_to_excel(data, 'audit_logs.xlsx', headers, 'Audit Logs')
        elif export_format == 'pdf':
            return ExportService.export_to_pdf(data, 'audit_logs.pdf', 'Audit Logs Report', headers)
        else:
            messages.error(request, 'Invalid export format.')
            return redirect('audit:log')
    except Exception as e:
        messages.error(request, f'Export failed: {str(e)}')
        return redirect('audit:log')
