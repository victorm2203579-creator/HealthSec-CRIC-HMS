"""alerts/views – Views for alert and incident management."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q

from audit.utils import log_event
from audit.models import AuditLog
from .models import Alert, Incident
from .services import AlertService


@login_required
def alert_dashboard(request):
    """Alert and incident response dashboard with KPIs and metrics."""
    stats = AlertService.get_statistics(days=30)

    open_alerts = Alert.objects.open().select_related('affected_system', 'assigned_to')[:5]
    open_incidents = Incident.objects.open().select_related('incident_commander')[:5]
    recent_alerts = Alert.objects.select_related('affected_system')[:10]

    context = {
        'stats': stats,
        'open_alerts': open_alerts,
        'open_incidents': open_incidents,
        'recent_alerts': recent_alerts,
    }
    return render(request, 'alerts/alert_dashboard.html', context)


@login_required
def alert_list(request):
    """List alerts with filtering and pagination."""
    severity_filter = request.GET.get('severity', '')
    status_filter = request.GET.get('status', '')
    assigned_filter = request.GET.get('assigned_to', '')
    search_query = request.GET.get('q', '')

    qs = Alert.objects.select_related('affected_system', 'assigned_to', 'resolved_by').order_by('-created_at')

    if severity_filter:
        qs = qs.filter(severity=severity_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if assigned_filter:
        if assigned_filter == 'me':
            qs = qs.filter(assigned_to=request.user)
        elif assigned_filter == 'unassigned':
            qs = qs.filter(assigned_to__isnull=True)
    if search_query:
        qs = qs.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'alerts': page_obj.object_list,
        'severity_choices': Alert.Severity.choices,
        'status_choices': Alert.Status.choices,
        'severity_filter': severity_filter,
        'status_filter': status_filter,
        'assigned_filter': assigned_filter,
        'search_query': search_query,
    }
    return render(request, 'alerts/alert_list.html', context)


@login_required
def alert_detail(request, pk):
    """Detail view for a single alert with action options."""
    alert = get_object_or_404(
        Alert.objects.select_related('affected_system', 'assigned_to', 'source_event',
                                     'acknowledged_by', 'resolved_by'),
        pk=pk,
    )

    if not alert.is_read:
        alert.mark_as_read(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'acknowledge' and alert.status == Alert.Status.NEW:
            AlertService.acknowledge_alert(alert, request.user)
            AlertService.notify_stakeholders(alert, 'acknowledged')
            messages.success(request, 'Alert acknowledged.')

        elif action == 'resolve':
            resolution_status = request.POST.get('resolution_status', Alert.Status.RESOLVED)
            notes = request.POST.get('notes', '')
            AlertService.resolve_alert(alert, request.user, resolution_status, notes)
            AlertService.notify_stakeholders(alert, 'resolved')
            messages.success(request, f'Alert marked as {resolution_status}.')

        elif action == 'assign':
            alert.assigned_to = request.user
            alert.save(update_fields=['assigned_to'])
            log_event(
                action='ALERT_ASSIGNED',
                description=f'Alert assigned to {request.user.username}',
                action_category=AuditLog.ActionCategory.ALERT,
                target_model='Alert',
                target_id=str(alert.pk)
            )
            messages.success(request, 'Alert assigned to you.')

        return redirect('alerts:alert_detail', pk=alert.pk)

    tags_list = [t.strip() for t in alert.tags.split(',') if t.strip()] if alert.tags else []

    context = {
        'alert': alert,
        'tags_list': tags_list,
        'severity_choices': Alert.Severity.choices,
        'status_choices': Alert.Status.choices,
    }
    return render(request, 'alerts/alert_detail.html', context)


@login_required
def incident_list(request):
    """List incidents with filtering and pagination."""
    phase_filter = request.GET.get('phase', '')
    commander_filter = request.GET.get('commander', '')
    search_query = request.GET.get('q', '')

    qs = Incident.objects.select_related('incident_commander', 'created_by').order_by('-detected_at')

    if phase_filter:
        qs = qs.filter(phase=phase_filter)
    if commander_filter:
        if commander_filter == 'me':
            qs = qs.filter(incident_commander=request.user)
        elif commander_filter == 'unassigned':
            qs = qs.filter(incident_commander__isnull=True)
    if search_query:
        qs = qs.filter(Q(title__icontains=search_query) | Q(incident_number__icontains=search_query))

    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'incidents': page_obj.object_list,
        'phase_choices': Incident.Phase.choices,
        'phase_filter': phase_filter,
        'commander_filter': commander_filter,
        'search_query': search_query,
    }
    return render(request, 'alerts/incident_list.html', context)


@login_required
def incident_detail(request, pk):
    """Detail view for a single incident with phase transitions."""
    incident = get_object_or_404(
        Incident.objects.select_related('incident_commander', 'created_by').prefetch_related('alerts'),
        pk=pk,
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'transition_phase':
            new_phase = request.POST.get('phase')
            notes = request.POST.get('notes', '')
            if new_phase in dict(Incident.Phase.choices):
                incident.transition_phase(new_phase, request.user, notes)
                messages.success(request, f'Incident moved to {new_phase} phase.')

        elif action == 'assign_commander':
            incident.incident_commander = request.user
            incident.save(update_fields=['incident_commander'])
            incident.add_timeline_entry('Commander assigned', request.user, f'Assigned to {request.user.username}')
            messages.success(request, 'You are now the incident commander.')

        elif action == 'add_alert':
            alert_id = request.POST.get('alert_id')
            try:
                alert = Alert.objects.get(pk=alert_id)
                incident.alerts.add(alert)
                incident.add_timeline_entry('Alert added', request.user, f'Added alert {alert.pk}')
                messages.success(request, 'Alert added to incident.')
            except Alert.DoesNotExist:
                messages.error(request, 'Alert not found.')

        return redirect('alerts:incident_detail', pk=incident.pk)

    available_alerts = Alert.objects.exclude(incidents=incident).order_by('-created_at')[:20]

    context = {
        'incident': incident,
        'phase_choices': Incident.Phase.choices,
        'available_alerts': available_alerts,
    }
    return render(request, 'alerts/incident_detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def incident_create(request):
    """Create a new incident from selected alerts."""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        alert_ids = request.POST.getlist('alert_ids')

        if not title or not description:
            messages.error(request, 'Title and description are required.')
            return redirect('alerts:incident_create')

        alerts = Alert.objects.filter(pk__in=alert_ids)

        incident = AlertService.create_incident(
            title=title,
            description=description,
            alerts=alerts,
            incident_commander=request.user if request.POST.get('self_assign') else None,
            created_by=request.user
        )

        log_event(
            action='INCIDENT_CREATED',
            description=f'Incident {incident.incident_number} created by {request.user.username}',
            action_category=AuditLog.ActionCategory.ALERT,
            target_model='Incident',
            target_id=str(incident.pk)
        )

        messages.success(request, f'Incident {incident.incident_number} created successfully.')
        return redirect('alerts:incident_detail', pk=incident.pk)

    open_alerts = Alert.objects.open().select_related('affected_system', 'assigned_to').order_by('-created_at')

    context = {
        'open_alerts': open_alerts,
    }
    return render(request, 'alerts/incident_create.html', context)


@login_required
@require_http_methods(['GET'])
def unread_alerts_count(request):
    """API endpoint returning count of unread alerts for current user."""
    count = Alert.objects.unread().count()
    return JsonResponse({'count': count, 'success': True})


@login_required
@require_http_methods(['POST'])
def mark_all_alerts_read(request):
    """Mark all NEW alerts as ACKNOWLEDGED — clears the notification badge."""
    updated = Alert.objects.filter(status=Alert.Status.NEW).update(
        status=Alert.Status.ACKNOWLEDGED
    )
    log_event(
        action='ALERTS_MARK_ALL_READ',
        description=f'{updated} alert(s) marked as acknowledged.',
        user=request.user,
        request=request,
        action_category='ALERT',
    )
    return JsonResponse({'ok': True, 'count': updated})


@login_required
@require_http_methods(['GET', 'POST'])
def test_email(request):
    """Test email configuration by sending a test email to the current user."""
    from django.contrib.auth.decorators import user_passes_test

    def is_admin(user):
        return user.is_staff or user.role == 'ADMIN'

    if not is_admin(request.user):
        messages.error(request, 'Only administrators can send test emails.')
        return redirect('alerts:dashboard')

    if request.method == 'POST':
        email_address = request.POST.get('email_address', request.user.email)

        if not email_address:
            messages.error(request, 'No email address provided.')
            return redirect('alerts:test_email')

        success = AlertService.send_test_email(email_address)

        if success:
            messages.success(
                request,
                f'Test email sent successfully to {email_address}. Check your inbox or email logs.'
            )
        else:
            messages.error(
                request,
                'Failed to send test email. Check your email configuration and try again.'
            )

        return redirect('alerts:test_email')

    context = {
        'default_email': request.user.email,
    }
    return render(request, 'alerts/test_email.html', context)
