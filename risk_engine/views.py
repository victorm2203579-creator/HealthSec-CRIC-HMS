"""
risk_engine/views.py
====================
Views for the Cyber Risk Intelligence Engine.

View inventory
--------------
Preserved (same URL names, updated implementations):
  risk_dashboard        – KPI summary + trend chart + current risk level
  compute_risk_score    – POST trigger for legacy RiskScore computation
  vulnerability_list    – VulnerabilityRecord list with CVSS bars + patch action
  threat_intel_list     – ThreatFeed IOC table (replaces old ThreatIntelFeed view)

New:
  threat_event_list     – Filterable ThreatEvent table with status update
  threat_event_detail   – Single threat detail with indicators + MITRE + mitigations
  mark_patched          – POST: mark a VulnerabilityRecord as patched
  risk_assessment       – Assessment history + generate trigger
  generate_assessment   – POST handler for generating a new RiskAssessment
"""

import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from audit.utils import log_event
from monitoring.models import HealthcareSystem
from .constants import THREAT_MITIGATIONS
from .engine import RiskIntelligenceEngine
from .models import (
    RiskAssessment,
    RiskScore,
    ThreatEvent,
    ThreatFeed,
    ThreatIntelFeed,
    Vulnerability,
    VulnerabilityRecord,
)
from .services import RiskScoringService

User = get_user_model()
_engine = RiskIntelligenceEngine()


# ---------------------------------------------------------------------------
# 1. Risk Dashboard
# ---------------------------------------------------------------------------

@login_required
def risk_dashboard(request):
    """
    Main risk intelligence dashboard.

    Displays:
    - Overall risk score (from open ThreatEvents) + colour-coded level badge
    - KPI cards: open threats, critical count, unpatched vulns, last assessment
    - 30-day threat trend chart
    - Most recent 10 threat events
    """
    open_events = ThreatEvent.objects.filter(
        status__in=[ThreatEvent.Status.OPEN, ThreatEvent.Status.INVESTIGATING]
    )
    overall_score = _engine.calculate_risk_score(open_events)
    risk_level = _engine.classify_risk_level(overall_score)

    critical_count = open_events.filter(severity=ThreatEvent.Severity.CRITICAL).count()
    high_count = open_events.filter(severity=ThreatEvent.Severity.HIGH).count()
    unpatched_vulns = VulnerabilityRecord.objects.filter(patched=False).count()
    last_assessment = RiskAssessment.objects.first()

    # Trend data (30 days)
    timeline = _engine.get_threat_timeline(days=30)
    trend_labels = list(timeline.keys())
    trend_values = list(timeline.values())

    # Severity distribution for doughnut chart
    sev_counts = {
        'LOW':      open_events.filter(severity=ThreatEvent.Severity.LOW).count(),
        'MEDIUM':   open_events.filter(severity=ThreatEvent.Severity.MEDIUM).count(),
        'HIGH':     open_events.filter(severity=ThreatEvent.Severity.HIGH).count(),
        'CRITICAL': open_events.filter(severity=ThreatEvent.Severity.CRITICAL).count(),
    }

    recent_events = (
        ThreatEvent.objects
        .select_related('target_user', 'assigned_to')
        .filter(status__in=[ThreatEvent.Status.OPEN, ThreatEvent.Status.INVESTIGATING])
        .order_by('-detected_at')[:10]
    )

    # Legacy RiskScore section
    legacy_scores = RiskScore.objects.select_related('system').order_by('-computed_at')[:5]
    systems = HealthcareSystem.objects.order_by('name')

    risk_level_badge = {
        'LOW':      'badge-low',
        'MEDIUM':   'badge-medium',
        'HIGH':     'badge-high',
        'CRITICAL': 'badge-critical',
    }.get(risk_level, 'secondary')

    return render(request, 'risk_engine/dashboard.html', {
        'overall_score': round(overall_score, 1),
        'risk_level': risk_level,
        'risk_level_badge': risk_level_badge,
        'open_count': open_events.count(),
        'critical_count': critical_count,
        'high_count': high_count,
        'unpatched_vulns': unpatched_vulns,
        'last_assessment': last_assessment,
        'recent_events': recent_events,
        'legacy_scores': legacy_scores,
        'systems': systems,
        'trend_labels_json': json.dumps(trend_labels),
        'trend_values_json': json.dumps(trend_values),
        'sev_counts_json': json.dumps(sev_counts),
    })


# ---------------------------------------------------------------------------
# Legacy: compute risk score for a HealthcareSystem (preserved)
# ---------------------------------------------------------------------------

@login_required
def compute_risk_score(request, system_pk):
    """Trigger a new RiskScore computation for a HealthcareSystem (POST only)."""
    if request.method == 'POST':
        system = get_object_or_404(HealthcareSystem, pk=system_pk)
        service = RiskScoringService()
        score = service.compute(system, user=request.user)
        messages.success(
            request,
            f'Risk score computed for {system.name}: {score.score} ({score.risk_level})',
        )
    return redirect('risk_engine:risk_dashboard')


# ---------------------------------------------------------------------------
# 2. Threat Event List
# ---------------------------------------------------------------------------

@login_required
def threat_event_list(request):
    """
    Filterable, paginated list of ThreatEvent records.

    Filters: threat_type, severity, status, date_from, date_to.
    Analysts can update a threat's status inline via POST.
    """
    if request.method == 'POST' and request.user.is_analyst:
        event_id = request.POST.get('event_id')
        new_status = request.POST.get('status')
        if event_id and new_status in ThreatEvent.Status.values:
            evt = get_object_or_404(ThreatEvent, pk=event_id)
            old_status = evt.status
            evt.status = new_status
            if new_status == ThreatEvent.Status.INVESTIGATING and not evt.assigned_to:
                evt.assigned_to = request.user
            evt.save(update_fields=['status', 'assigned_to'])
            log_event(
                'OTHER',
                f'ThreatEvent #{event_id} status changed from {old_status} to {new_status}.',
                request=request,
            )
            messages.success(request, f'Threat status updated to {new_status}.')
        return redirect('risk_engine:threat_event_list')

    qs = ThreatEvent.objects.select_related('target_user', 'assigned_to').order_by('-detected_at')

    # Filters
    f_type     = request.GET.get('threat_type', '')
    f_severity = request.GET.get('severity', '')
    f_status   = request.GET.get('status', '')
    f_from     = request.GET.get('date_from', '')
    f_to       = request.GET.get('date_to', '')

    if f_type:
        qs = qs.filter(threat_type=f_type)
    if f_severity:
        qs = qs.filter(severity=int(f_severity))
    if f_status:
        qs = qs.filter(status=f_status)
    if f_from:
        qs = qs.filter(detected_at__date__gte=f_from)
    if f_to:
        qs = qs.filter(detected_at__date__lte=f_to)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    analysts = User.objects.filter(role__in=['ANALYST', 'COMPLIANCE', 'ADMIN'], is_active=True)

    return render(request, 'risk_engine/threat_list.html', {
        'page_obj': page_obj,
        'threat_type_choices': ThreatEvent.ThreatType.choices,
        'severity_choices': ThreatEvent.Severity.choices,
        'status_choices': ThreatEvent.Status.choices,
        'analysts': analysts,
        'f_type': f_type,
        'f_severity': f_severity,
        'f_status': f_status,
        'f_from': f_from,
        'f_to': f_to,
        'total_count': qs.count(),
    })


# ---------------------------------------------------------------------------
# 3. Threat Event Detail
# ---------------------------------------------------------------------------

@login_required
def threat_event_detail(request, pk):
    """
    Full detail view for a single ThreatEvent.

    Shows raw indicator JSON (formatted), MITRE ATT&CK tactic, status timeline
    (simulated from detected_at), and recommended mitigations from constants.py.
    Analysts can update status and assign to a user from this view.
    """
    event = get_object_or_404(
        ThreatEvent.objects.select_related('target_user', 'assigned_to'),
        pk=pk,
    )

    if request.method == 'POST' and request.user.is_analyst:
        new_status = request.POST.get('status', '')
        assign_to_id = request.POST.get('assign_to', '')

        if new_status and new_status in ThreatEvent.Status.values:
            event.status = new_status
        if assign_to_id:
            try:
                event.assigned_to = User.objects.get(pk=assign_to_id)
            except User.DoesNotExist:
                pass
        event.save(update_fields=['status', 'assigned_to'])
        messages.success(request, 'Threat event updated.')
        log_event(
            'OTHER',
            f'ThreatEvent {event.threat_id} updated: status={event.status}.',
            request=request,
        )

    mitigations = THREAT_MITIGATIONS.get(event.threat_type, [])
    indicators_pretty = json.dumps(event.indicators, indent=2) if event.indicators else '{}'
    analysts = User.objects.filter(role__in=['ANALYST', 'COMPLIANCE', 'ADMIN'], is_active=True)

    return render(request, 'risk_engine/threat_detail.html', {
        'event': event,
        'mitigations': mitigations,
        'indicators_pretty': indicators_pretty,
        'status_choices': ThreatEvent.Status.choices,
        'analysts': analysts,
    })


# ---------------------------------------------------------------------------
# 4. Vulnerability Records List (new model)
# ---------------------------------------------------------------------------

@login_required
def vulnerability_list(request):
    """
    CVE-style VulnerabilityRecord list with CVSS score progress bars.

    Filterable by severity and patch status.  Analysts can mark records
    as patched via the inline form.
    """
    qs = VulnerabilityRecord.objects.order_by('-cvss_score', '-discovered_at')

    f_severity = request.GET.get('severity', '')
    f_patched  = request.GET.get('patched', '')

    if f_severity:
        qs = qs.filter(severity=f_severity)
    if f_patched == 'yes':
        qs = qs.filter(patched=True)
    elif f_patched == 'no':
        qs = qs.filter(patched=False)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'risk_engine/vulnerabilities.html', {
        'page_obj': page_obj,
        'severity_choices': VulnerabilityRecord.Severity.choices,
        'f_severity': f_severity,
        'f_patched': f_patched,
        'total_count': qs.count(),
        'unpatched_count': VulnerabilityRecord.objects.filter(patched=False).count(),
        'critical_count': VulnerabilityRecord.objects.filter(
            severity='CRITICAL', patched=False,
        ).count(),
    })


@login_required
def mark_patched(request, pk):
    """Mark a VulnerabilityRecord as patched (POST, analyst+ only)."""
    if not request.user.is_analyst:
        return HttpResponseForbidden('Analyst role required.')
    if request.method != 'POST':
        return redirect('risk_engine:vulnerability_list')

    vuln = get_object_or_404(VulnerabilityRecord, pk=pk)
    if not vuln.patched:
        vuln.patched = True
        vuln.patched_at = timezone.now()
        vuln.patch_notes = request.POST.get('patch_notes', '').strip() or 'Marked as patched via dashboard.'
        vuln.save(update_fields=['patched', 'patched_at', 'patch_notes'])
        log_event(
            'OTHER',
            f'VulnerabilityRecord {vuln.cve_reference or vuln.pk} marked as patched.',
            request=request,
        )
        messages.success(request, f'{vuln.title} marked as patched.')
    return redirect('risk_engine:vulnerability_list')


# ---------------------------------------------------------------------------
# 5. Threat Feed View (uses new ThreatFeed model)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 6. Risk Assessment View
# ---------------------------------------------------------------------------

@login_required
def risk_assessment(request):
    """
    Risk assessment history and generation trigger.

    GET: Shows all past assessments with a risk trend chart.
    POST: Triggers generate_risk_assessment() and redirects back.
    """
    if request.method == 'POST':
        return redirect('risk_engine:generate_assessment')

    assessments = RiskAssessment.objects.select_related('conducted_by').order_by('-conducted_at')
    paginator = Paginator(assessments, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Risk score trend over past assessments (last 15)
    recent = list(assessments[:15])[::-1]
    trend_labels = [a.conducted_at.strftime('%b %d') for a in recent]
    trend_values = [a.overall_risk_score for a in recent]

    return render(request, 'risk_engine/assessment.html', {
        'page_obj': page_obj,
        'trend_labels_json': json.dumps(trend_labels),
        'trend_values_json': json.dumps(trend_values),
        'latest': assessments.first(),
    })


@login_required
def generate_assessment(request):
    """POST: Generate a new RiskAssessment and redirect to history."""
    if not request.user.is_analyst:
        messages.error(request, 'Analyst role required to generate assessments.')
        return redirect('risk_engine:risk_assessment')
    if request.method != 'POST':
        return redirect('risk_engine:risk_assessment')

    result = _engine.generate_risk_assessment(requested_by=request.user)
    log_event(
        'OTHER',
        f"Risk assessment generated: {result['level']} ({result['score']:.1f}/100).",
        request=request,
    )
    messages.success(
        request,
        f"Assessment complete — risk level: {result['level']} ({result['score']:.1f}/100). "
        f"Next due: {result['next_due']}.",
    )
    return redirect('risk_engine:risk_assessment')


