"""
reports/views.py
================
Views for generating and downloading PDF reports.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from audit.utils import log_event
from compliance.models import ComplianceFramework, ControlAssessment
from risk_engine.models import RiskScore
from .models import GeneratedReport
from .services import PDFReportService

logger = logging.getLogger('healthsec.reports')


@login_required
def report_list(request):
    """List previously generated reports."""
    reports = GeneratedReport.objects.select_related('generated_by').order_by('-generated_at')
    return render(request, 'reports/report_list.html', {'reports': reports})


@login_required
def generate_risk_report(request):
    """Generate and stream a Risk Summary PDF."""
    scores = RiskScore.objects.select_related('system').order_by('-computed_at')[:50]

    service = PDFReportService(
        title='Risk Summary Report',
        subtitle=f'Generated for: {request.user.get_full_name() or request.user.username}',
        author=request.user.get_full_name() or request.user.username,
    )

    try:
        pdf_bytes = service.build_risk_summary(list(scores))
    except Exception as exc:
        logger.error('PDF generation failed: %s', exc)
        messages.error(request, 'Report generation failed. Please try again.')
        return redirect('reports:report_list')

    log_event(
        user=request.user,
        action='REPORT_GENERATED',
        description='Risk Summary Report generated.',
        request=request,
    )

    filename = f'risk_report_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def generate_compliance_report(request, framework_pk):
    """Generate and stream a Compliance Status PDF for a specific framework."""
    try:
        framework = ComplianceFramework.objects.get(pk=framework_pk)
    except ComplianceFramework.DoesNotExist:
        messages.error(request, 'Framework not found.')
        return redirect('reports:report_list')

    assessments = ControlAssessment.objects.filter(
        control__framework=framework
    ).select_related('control').order_by('control__control_id')

    service = PDFReportService(
        title=f'Compliance Report – {framework.short_name}',
        author=request.user.get_full_name() or request.user.username,
    )

    try:
        pdf_bytes = service.build_compliance_report(framework, list(assessments))
    except Exception as exc:
        logger.error('PDF generation failed: %s', exc)
        messages.error(request, 'Report generation failed. Please try again.')
        return redirect('reports:report_list')

    log_event(
        user=request.user,
        action='REPORT_GENERATED',
        description=f'Compliance report generated for {framework.short_name}.',
        request=request,
    )

    filename = f'compliance_{framework.short_name}_{timezone.now().strftime("%Y%m%d")}.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
