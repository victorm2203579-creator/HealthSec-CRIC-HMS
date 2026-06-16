"""
monitoring/views.py
===================
Views for the healthcare information monitoring section.

View inventory
--------------
Existing infrastructure views:
  system_list       – list all monitored healthcare systems
  system_detail     – single system with recent events
  event_list        – all monitoring events with severity filter

New patient-record monitoring views:
  monitoring_dashboard      – real-time activity feed and KPI cards
  record_access_list        – full paginated access log with CSV export
  suspicious_activity_list  – suspicious events with resolve action
  resolve_suspicious        – POST handler to resolve a suspicious activity
  patient_record_list       – list/create simulated patient records
  patient_record_detail     – view one record (creates RecordAccessLog)
  user_activity             – per-user access heatmap and risk profile
"""

import csv
import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from audit.utils import log_event
from .engine import MonitoringEngine
from .models import (
    DataAsset,
    HealthcareSystem,
    MonitoringEvent,
    PatientRecord,
    RecordAccessLog,
    SuspiciousActivity,
)

User = get_user_model()
engine = MonitoringEngine()


# ---------------------------------------------------------------------------
# Existing infrastructure views
# ---------------------------------------------------------------------------

@login_required
def system_list(request):
    """Display all monitored healthcare systems."""
    systems = HealthcareSystem.objects.select_related('owner').all()
    return render(request, 'monitoring/system_list.html', {'systems': systems})


@login_required
def system_detail(request, pk):
    """Detail view for a single healthcare system with its recent events."""
    system = get_object_or_404(HealthcareSystem, pk=pk)
    events = system.events.order_by('-occurred_at')[:50]
    return render(request, 'monitoring/system_detail.html', {
        'system': system,
        'events': events,
    })


@login_required
def event_list(request):
    """List all monitoring events with optional severity filter."""
    severity = request.GET.get('severity', '')
    qs = MonitoringEvent.objects.select_related('system').order_by('-occurred_at')
    if severity:
        qs = qs.filter(severity=severity)
    return render(request, 'monitoring/event_list.html', {
        'events': qs[:100],
        'severity_filter': severity,
        'severity_choices': MonitoringEvent.Severity.choices,
    })


# ---------------------------------------------------------------------------
# Monitoring Dashboard
# ---------------------------------------------------------------------------

@login_required
def monitoring_dashboard(request):
    """
    Real-time activity monitoring dashboard.

    Shows summary KPI cards, a recent access log table (last 50 entries),
    and filter controls for date / user / record type / suspicious-only.
    """
    today = timezone.now().date()

    # --- KPI counts ---
    total_today = RecordAccessLog.objects.filter(timestamp__date=today).count()
    suspicious_today = RecordAccessLog.objects.filter(
        timestamp__date=today, is_suspicious=True
    ).count()
    flagged_records = PatientRecord.objects.filter(is_flagged=True).count()
    active_users = (
        RecordAccessLog.objects.filter(timestamp__date=today)
        .values('user').distinct().count()
    )
    unresolved_suspicious = SuspiciousActivity.objects.filter(resolved=False).count()

    # --- Filters from GET params ---
    filter_date = request.GET.get('date', '')
    filter_user = request.GET.get('user', '')
    filter_record_type = request.GET.get('record_type', '')
    filter_suspicious = request.GET.get('suspicious_only', '')

    logs_qs = (
        RecordAccessLog.objects
        .select_related('user', 'patient_record')
        .order_by('-timestamp')
    )

    if filter_date:
        logs_qs = logs_qs.filter(timestamp__date=filter_date)
    if filter_user:
        logs_qs = logs_qs.filter(user__username__icontains=filter_user)
    if filter_record_type:
        logs_qs = logs_qs.filter(patient_record__record_type=filter_record_type)
    if filter_suspicious:
        logs_qs = logs_qs.filter(is_suspicious=True)

    recent_logs = logs_qs[:50]

    # --- Hourly chart data for today ---
    hourly_counts = [0] * 24
    today_logs = RecordAccessLog.objects.filter(timestamp__date=today)
    for h in today_logs.values_list('access_hour', flat=True):
        if 0 <= h <= 23:
            hourly_counts[h] += 1

    return render(request, 'monitoring/dashboard.html', {
        'total_today': total_today,
        'suspicious_today': suspicious_today,
        'flagged_records': flagged_records,
        'active_users': active_users,
        'unresolved_suspicious': unresolved_suspicious,
        'recent_logs': recent_logs,
        'record_type_choices': PatientRecord.RecordType.choices,
        'filter_date': filter_date,
        'filter_user': filter_user,
        'filter_record_type': filter_record_type,
        'filter_suspicious': filter_suspicious,
        'hourly_counts_json': json.dumps(hourly_counts),
    })


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Suspicious Activity
# ---------------------------------------------------------------------------

@login_required
def suspicious_activity_list(request):
    """
    List all suspicious activities.

    Filterable by resolved status, severity, and activity type.
    Analysts and above can mark activities as resolved.
    """
    qs = (
        SuspiciousActivity.objects
        .select_related('user', 'related_record', 'resolved_by')
        .order_by('-timestamp')
    )

    filter_resolved = request.GET.get('resolved', '')
    filter_severity = request.GET.get('severity', '')
    filter_type = request.GET.get('activity_type', '')

    if filter_resolved == 'yes':
        qs = qs.filter(resolved=True)
    elif filter_resolved == 'no':
        qs = qs.filter(resolved=False)
    if filter_severity:
        qs = qs.filter(severity=filter_severity)
    if filter_type:
        qs = qs.filter(activity_type=filter_type)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'monitoring/suspicious.html', {
        'page_obj': page_obj,
        'severity_choices': SuspiciousActivity.Severity.choices,
        'activity_type_choices': SuspiciousActivity.ActivityType.choices,
        'filter_resolved': filter_resolved,
        'filter_severity': filter_severity,
        'filter_type': filter_type,
        'unresolved_count': SuspiciousActivity.objects.filter(resolved=False).count(),
    })


@login_required
def resolve_suspicious(request, pk):
    """
    POST handler to mark a SuspiciousActivity as resolved.

    Restricted to ANALYST role and above.
    """
    if not request.user.is_analyst:
        return HttpResponseForbidden('Analyst role required.')
    if request.method != 'POST':
        return redirect('monitoring:suspicious_activity_list')

    activity = get_object_or_404(SuspiciousActivity, pk=pk)
    if not activity.resolved:
        activity.resolved = True
        activity.resolved_by = request.user
        activity.resolved_at = timezone.now()
        activity.save(update_fields=['resolved', 'resolved_by', 'resolved_at'])
        log_event(
            'OTHER',
            f'Resolved suspicious activity #{pk}: {activity.get_activity_type_display()}.',
            request=request,
        )
        messages.success(request, f'Activity #{pk} marked as resolved.')

    return redirect('monitoring:suspicious_activity_list')


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _log_access(request, record, access_type):
    """
    Create a RecordAccessLog for the given request and patient record.

    Extracts IP address, session key, User-Agent, and the current hour
    automatically from the request.

    Args:
        request:     The current HttpRequest.
        record:      The PatientRecord being accessed.
        access_type: A RecordAccessLog.AccessType value.

    Returns:
        RecordAccessLog: the newly created (and saved) log instance.
    """
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR', '127.0.0.1')
    )
    device_info = request.META.get('HTTP_USER_AGENT', '')[:255]
    session_key = (request.session.session_key or '')[:40]
    current_hour = timezone.now().hour

    return RecordAccessLog.objects.create(
        user=request.user,
        patient_record=record,
        access_type=access_type,
        ip_address=ip or None,
        device_info=device_info,
        access_hour=current_hour,
        session_key=session_key,
    )
