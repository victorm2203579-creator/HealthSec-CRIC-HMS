"""
compliance/views.py
===================
Views for the Compliance Management Module.

View inventory
--------------
New (compliance engine):
  compliance_dashboard   – Overall score gauge, per-framework breakdown, run button
  control_list           – All ComplianceControls with latest results; filterable
  run_compliance_check   – POST: trigger ComplianceChecker.run_all_automated_checks()
  compliance_reports     – History of ComplianceReport snapshots
  remediation_view       – FAIL/PARTIAL controls with manual status override

Legacy (preserved URL names):
  framework_list         – All ComplianceFramework records
  framework_detail       – Single framework + its legacy Controls
  control_detail         – Single legacy Control + assessment history
  compliance_summary     – Redirect alias → compliance_dashboard
"""

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from audit.utils import log_event
from .checker import ComplianceChecker
from .models import (
    ComplianceCheckResult,
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    Control,
    ControlAssessment,
)


# ---------------------------------------------------------------------------
# 1. Compliance Dashboard
# ---------------------------------------------------------------------------

@login_required
def compliance_dashboard(request):
    """
    Overall compliance posture dashboard.

    Displays:
    - Weighted overall score across all active frameworks
    - Per-framework compliance score and level badge
    - Pass/Fail/Partial breakdown donut chart data
    - Most recent check results
    - "Run Automated Check" trigger button
    """
    frameworks = ComplianceFramework.objects.filter(is_active=True).prefetch_related('engine_controls')

    # Build per-framework summary
    framework_summaries = []
    total_controls = 0
    total_pass = 0
    total_fail = 0
    total_partial = 0
    total_pending = 0

    for fw in frameworks:
        controls = fw.engine_controls.all()
        fw_total = controls.count()
        fw_pass = fw_fail = fw_partial = fw_pending = 0

        for ctrl in controls:
            result = ctrl.results.order_by('-checked_at').first()
            if result:
                if result.status == ComplianceCheckResult.CheckStatus.PASS:
                    fw_pass += 1
                elif result.status == ComplianceCheckResult.CheckStatus.FAIL:
                    fw_fail += 1
                elif result.status == ComplianceCheckResult.CheckStatus.PARTIAL:
                    fw_partial += 1
                else:
                    fw_pending += 1
            else:
                fw_pending += 1

        score = fw.get_compliance_score()
        level = fw.get_compliance_level()

        framework_summaries.append({
            'framework': fw,
            'score': round(score, 1),
            'level': level,
            'total': fw_total,
            'pass': fw_pass,
            'fail': fw_fail,
            'partial': fw_partial,
            'pending': fw_pending,
        })

        total_controls += fw_total
        total_pass += fw_pass
        total_fail += fw_fail
        total_partial += fw_partial
        total_pending += fw_pending

    # Overall weighted score (average of framework scores)
    overall_score = 0.0
    if framework_summaries:
        active_summaries = [s for s in framework_summaries if s['total'] > 0]
        if active_summaries:
            overall_score = sum(s['score'] for s in active_summaries) / len(active_summaries)

    overall_level = ComplianceReport.level_from_score(overall_score)

    # Donut chart data
    donut_data = {
        'pass': total_pass,
        'fail': total_fail,
        'partial': total_partial,
        'pending': total_pending,
    }

    # Per-framework bar chart data
    fw_labels = [s['framework'].short_name for s in framework_summaries]
    fw_scores = [s['score'] for s in framework_summaries]

    # Recent 15 check results
    recent_results = (
        ComplianceCheckResult.objects
        .select_related('control', 'control__framework', 'checked_by')
        .order_by('-checked_at')[:15]
    )

    latest_report = ComplianceReport.objects.order_by('-generated_at').first()

    return render(request, 'compliance/dashboard.html', {
        'framework_summaries': framework_summaries,
        'overall_score': round(overall_score, 1),
        'overall_level': overall_level,
        'total_controls': total_controls,
        'total_pass': total_pass,
        'total_fail': total_fail,
        'total_partial': total_partial,
        'total_pending': total_pending,
        'recent_results': recent_results,
        'latest_report': latest_report,
        'donut_data_json': json.dumps(donut_data),
        'fw_labels_json': json.dumps(fw_labels),
        'fw_scores_json': json.dumps(fw_scores),
    })


# Legacy alias
@login_required
def compliance_summary(request):
    """Redirect legacy URL to the new compliance dashboard."""
    return redirect('compliance:dashboard')


# ---------------------------------------------------------------------------
# 2. Run Compliance Check (POST)
# ---------------------------------------------------------------------------

@login_required
def run_compliance_check(request):
    """
    POST endpoint that triggers ComplianceChecker.run_all_automated_checks().

    Requires compliance officer or admin role.
    After running checks, creates a ComplianceReport snapshot and redirects
    to the dashboard with a summary message.
    """
    if not request.user.is_compliance_officer:
        return HttpResponseForbidden('Compliance Officer role required.')
    if request.method != 'POST':
        return redirect('compliance:dashboard')

    checker = ComplianceChecker()
    run_result = checker.run_all_automated_checks(triggered_by=request.user)

    # Persist a ComplianceReport per framework
    frameworks = ComplianceFramework.objects.filter(is_active=True)
    for fw in frameworks:
        controls = fw.engine_controls.all()
        fw_total = controls.count()
        if fw_total == 0:
            continue
        fw_pass = fw_fail = 0
        for ctrl in controls:
            result = ctrl.results.order_by('-checked_at').first()
            if result:
                if result.status == 'PASS':
                    fw_pass += 1
                elif result.status == 'FAIL':
                    fw_fail += 1

        fw_score = fw.get_compliance_score()
        ComplianceReport.objects.create(
            framework=fw,
            generated_by=request.user,
            overall_score=fw_score,
            compliance_level=ComplianceReport.level_from_score(fw_score),
            total_controls=fw_total,
            passed_controls=fw_pass,
            failed_controls=fw_fail,
            summary_json={
                'passed': fw_pass,
                'failed': fw_fail,
                'total': fw_total,
                'score': fw_score,
            },
        )

    log_event(
        'COMPLIANCE',
        f"Automated compliance check run by {request.user.username}: "
        f"score {run_result['overall_score']:.1f}%, "
        f"{run_result['passed']} passed, {run_result['failed']} failed.",
        request=request,
    )

    messages.success(
        request,
        f"Compliance check complete — overall score: {run_result['overall_score']:.1f}%. "
        f"{run_result['passed']} passed · {run_result['failed']} failed · "
        f"{run_result['partial']} partial · {run_result['pending']} pending."
    )
    return redirect('compliance:dashboard')


# ---------------------------------------------------------------------------
# 3. Compliance Control List
# ---------------------------------------------------------------------------

@login_required
def control_list(request):
    """
    Paginated, filterable list of all ComplianceControl records.

    Filters: framework, category, status (derived from latest check result).
    Each row shows the control's latest check result status and score.
    """
    qs = ComplianceControl.objects.select_related('framework').order_by('framework', 'control_code')

    f_framework = request.GET.get('framework', '')
    f_category  = request.GET.get('category', '')
    f_status    = request.GET.get('status', '')

    if f_framework:
        qs = qs.filter(framework__pk=f_framework)
    if f_category:
        qs = qs.filter(control_category=f_category)

    # Apply status filter by comparing against the latest result for each control
    if f_status:
        matching_pks = []
        for ctrl in qs:
            result = ctrl.results.order_by('-checked_at').first()
            if result and result.status == f_status:
                matching_pks.append(ctrl.pk)
            elif not result and f_status == 'PENDING':
                matching_pks.append(ctrl.pk)
        qs = ComplianceControl.objects.filter(pk__in=matching_pks).select_related('framework').order_by('framework', 'control_code')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Annotate each control with its latest result (for the template)
    for ctrl in page_obj:
        ctrl.latest_result = ctrl.results.order_by('-checked_at').first()

    return render(request, 'compliance/controls.html', {
        'page_obj': page_obj,
        'frameworks': ComplianceFramework.objects.filter(is_active=True),
        'category_choices': ComplianceControl.ControlCategory.choices,
        'status_choices': ComplianceCheckResult.CheckStatus.choices,
        'f_framework': f_framework,
        'f_category': f_category,
        'f_status': f_status,
        'total_count': qs.count(),
    })


# ---------------------------------------------------------------------------
# 4. Remediation View
# ---------------------------------------------------------------------------

@login_required
def remediation_view(request):
    """
    Lists all FAIL and PARTIAL compliance controls with remediation guidance.

    Compliance officers can manually override a control's status (e.g., after
    completing a remediation step) by submitting the inline POST form.
    The override creates a new ComplianceCheckResult with the chosen status.
    """
    if request.method == 'POST' and request.user.is_compliance_officer:
        control_pk = request.POST.get('control_pk')
        new_status  = request.POST.get('status')
        notes       = request.POST.get('notes', '').strip()

        if control_pk and new_status in ComplianceCheckResult.CheckStatus.values:
            ctrl = get_object_or_404(ComplianceControl, pk=control_pk)
            score_map = {'PASS': 100.0, 'PARTIAL': 60.0, 'FAIL': 0.0,
                         'NOT_APPLICABLE': 100.0, 'PENDING': 50.0}
            ComplianceCheckResult.objects.create(
                control=ctrl,
                checked_by=request.user,
                status=new_status,
                score=score_map.get(new_status, 50.0),
                notes=notes or f'Manual status override by {request.user.username}.',
                evidence=f'Manually set to {new_status} by {request.user.username} on {timezone.now():%Y-%m-%d}.',
                remediation_steps='',
            )
            log_event(
                'COMPLIANCE',
                f'Control {ctrl.control_code} manually updated to {new_status} by {request.user.username}.',
                request=request,
            )
            messages.success(request, f'{ctrl.title} updated to {new_status}.')
        return redirect('compliance:remediation')

    # Gather all controls whose latest result is FAIL or PARTIAL (or no result)
    all_controls = ComplianceControl.objects.select_related('framework').order_by('framework', 'control_code')
    remediation_items = []
    for ctrl in all_controls:
        result = ctrl.results.order_by('-checked_at').first()
        status = result.status if result else 'PENDING'
        if status in ('FAIL', 'PARTIAL', 'PENDING'):
            remediation_items.append({
                'control': ctrl,
                'latest_result': result,
                'status': status,
            })

    # Statistics
    fail_count    = sum(1 for i in remediation_items if i['status'] == 'FAIL')
    partial_count = sum(1 for i in remediation_items if i['status'] == 'PARTIAL')
    pending_count = sum(1 for i in remediation_items if i['status'] == 'PENDING')

    paginator = Paginator(remediation_items, 15)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'compliance/remediation.html', {
        'page_obj': page_obj,
        'fail_count': fail_count,
        'partial_count': partial_count,
        'pending_count': pending_count,
        'total_issues': len(remediation_items),
        'status_choices': ComplianceCheckResult.CheckStatus.choices,
    })


# ---------------------------------------------------------------------------
# 5. Compliance Reports
# ---------------------------------------------------------------------------

@login_required
def compliance_reports(request):
    """
    Historical list of ComplianceReport snapshots.

    Shows all past reports ordered by generation date.
    Compliance officers can trigger a new report (which runs all checks and
    creates a snapshot) via POST.  Compares the two most recent reports to
    show the score delta.
    """
    if request.method == 'POST' and request.user.is_compliance_officer:
        return redirect('compliance:run_check')

    reports_qs = ComplianceReport.objects.select_related('framework', 'generated_by').order_by('-generated_at')
    paginator  = Paginator(reports_qs, 15)
    page_obj   = paginator.get_page(request.GET.get('page', 1))

    # Score delta between the two most recent reports for each framework
    frameworks = ComplianceFramework.objects.filter(is_active=True)
    fw_deltas = []
    for fw in frameworks:
        fw_reports = ComplianceReport.objects.filter(framework=fw).order_by('-generated_at')[:2]
        if len(fw_reports) >= 2:
            delta = round(fw_reports[0].overall_score - fw_reports[1].overall_score, 1)
        else:
            delta = None
        latest = fw_reports[0] if fw_reports else None
        fw_deltas.append({'framework': fw, 'latest': latest, 'delta': delta})

    return render(request, 'compliance/reports.html', {
        'page_obj': page_obj,
        'fw_deltas': fw_deltas,
        'total_reports': reports_qs.count(),
    })


# ---------------------------------------------------------------------------
# Legacy views (preserved URL names for base.html sidebar links)
# ---------------------------------------------------------------------------

@login_required
def framework_list(request):
    """List all compliance frameworks (legacy view)."""
    from django.db.models import Count
    frameworks = ComplianceFramework.objects.filter(is_active=True).annotate(
        control_count=Count('controls')
    )
    return render(request, 'compliance/framework_list.html', {'frameworks': frameworks})


@login_required
def framework_detail(request, pk):
    """Single framework with its engine controls."""
    framework = get_object_or_404(ComplianceFramework, pk=pk)
    controls  = framework.engine_controls.prefetch_related('results').order_by('control_code')
    for ctrl in controls:
        ctrl.latest_result = ctrl.results.order_by('-checked_at').first()
    return render(request, 'compliance/framework_detail.html', {
        'framework': framework,
        'controls': controls,
    })


@login_required
def control_detail(request, pk):
    """Single legacy control with assessment history."""
    control     = get_object_or_404(Control, pk=pk)
    assessments = control.assessments.select_related('assessed_by').order_by('-assessed_at')
    return render(request, 'compliance/control_detail.html', {
        'control': control,
        'assessments': assessments,
    })
