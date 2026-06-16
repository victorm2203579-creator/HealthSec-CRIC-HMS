"""
reports/models.py
=================
Model to track generated reports so users can download previously
created PDFs without regenerating them each time.
"""

from django.db import models
from django.conf import settings


class GeneratedReport(models.Model):
    """Metadata record for a generated PDF or analytics report."""

    class ReportType(models.TextChoices):
        RISK_SUMMARY = 'RISK', 'Risk Summary Report'
        COMPLIANCE_STATUS = 'COMPLIANCE', 'Compliance Status Report'
        INCIDENT_REPORT = 'INCIDENT', 'Incident Report'
        AUDIT_LOG_EXPORT = 'AUDIT', 'Audit Log Export'
        VULNERABILITY_REPORT = 'VULN', 'Vulnerability Report'
        EXECUTIVE_SUMMARY = 'EXEC', 'Executive Summary'

    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    title = models.CharField(max_length=300)

    # The generated file stored in media/reports/
    file = models.FileField(upload_to='reports/', null=True, blank=True)

    # Parameters used to generate this report (date range, filters, etc.)
    parameters = models.JSONField(null=True, blank=True)

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports_generated_report'
        ordering = ['-generated_at']

    def __str__(self):
        return f'{self.title} ({self.generated_at:%Y-%m-%d})'
