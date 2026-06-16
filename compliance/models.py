"""
compliance/models.py
====================
Models for regulatory compliance management.

Model inventory
---------------
Legacy (preserved — used by existing migrations):
  ComplianceFramework   – Regulatory framework (HIPAA, NDPR, ISO 27001, …)
  Control               – Single control within a framework
  ControlAssessment     – Manual assessment result for a control
  ComplianceEvidence    – Documentary evidence for an assessment

New (compliance engine):
  ComplianceControl     – Engine-managed control with automated check support
  ComplianceCheckResult – Automated or manual check result per control
  ComplianceReport      – Point-in-time compliance snapshot per framework
"""

import uuid

from django.conf import settings
from django.db import models


# ---------------------------------------------------------------------------
# Legacy models (unchanged schemas — kept for migration continuity)
# ---------------------------------------------------------------------------

class ComplianceFramework(models.Model):
    """
    A regulatory framework or standard (e.g., HIPAA, NDPR, ISO 27001).

    Extended with framework_id (UUID) and applicable_region to support
    multi-region compliance tracking in the new engine.
    """

    # Stable UUID reference used by the new engine (added in migration 0002)
    framework_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    name = models.CharField(max_length=200, unique=True)
    short_name = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50, blank=True)
    issuing_body = models.CharField(max_length=100, blank=True)

    # Geographic / jurisdictional scope (e.g., "Nigeria", "USA", "Global")
    applicable_region = models.CharField(max_length=100, blank=True, default='Global')

    is_active = models.BooleanField(default=True)

    # Legacy field — kept for existing migrations
    created_at = models.DateTimeField(auto_now_add=True)

    # Alias used in views / templates
    @property
    def added_at(self):
        return self.created_at

    class Meta:
        db_table = 'compliance_framework'
        ordering = ['name']

    def __str__(self):
        return f'{self.short_name} – {self.name}'

    def get_compliance_score(self):
        """
        Return the latest weighted compliance score (0-100) for this framework,
        calculated from the most recent ComplianceCheckResult per control.
        """
        controls = self.engine_controls.filter(weight__gt=0)
        if not controls.exists():
            return 0.0
        total_weight = sum(c.weight for c in controls)
        if total_weight == 0:
            return 0.0
        weighted_sum = 0.0
        for ctrl in controls:
            result = ctrl.results.order_by('-checked_at').first()
            if result:
                weighted_sum += ctrl.weight * result.score
        return round((weighted_sum / total_weight), 1)

    def get_compliance_level(self):
        """Classify the framework score into a compliance level label."""
        score = self.get_compliance_score()
        if score >= 90:
            return 'FULLY_COMPLIANT'
        if score >= 70:
            return 'COMPLIANT'
        if score >= 40:
            return 'PARTIAL'
        return 'NON_COMPLIANT'


class Control(models.Model):
    """
    Legacy: a single control or requirement within a compliance framework.
    Superseded by ComplianceControl for new engine work; kept for data continuity.
    """

    class ControlCategory(models.TextChoices):
        ADMINISTRATIVE = 'ADMIN', 'Administrative'
        PHYSICAL = 'PHYSICAL', 'Physical'
        TECHNICAL = 'TECHNICAL', 'Technical'
        OPERATIONAL = 'OPS', 'Operational'

    framework = models.ForeignKey(
        ComplianceFramework,
        on_delete=models.CASCADE,
        related_name='controls',
    )
    control_id = models.CharField(max_length=50)
    title = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(max_length=10, choices=ControlCategory.choices)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        db_table = 'compliance_control'
        unique_together = ('framework', 'control_id')
        ordering = ['framework', 'control_id']

    def __str__(self):
        return f'{self.framework.short_name} – {self.control_id}: {self.title}'


class ControlAssessment(models.Model):
    """Legacy: manual assessment result for a Control."""

    class ComplianceStatus(models.TextChoices):
        COMPLIANT = 'COMPLIANT', 'Compliant'
        PARTIAL = 'PARTIAL', 'Partially Compliant'
        NON_COMPLIANT = 'NON_COMPLIANT', 'Non-Compliant'
        NOT_APPLICABLE = 'NA', 'Not Applicable'
        NOT_ASSESSED = 'NOT_ASSESSED', 'Not Yet Assessed'

    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name='assessments')
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='control_assessments',
    )
    status = models.CharField(
        max_length=20,
        choices=ComplianceStatus.choices,
        default=ComplianceStatus.NOT_ASSESSED,
    )
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    score = models.PositiveSmallIntegerField(default=0)
    assessed_at = models.DateTimeField(auto_now_add=True)
    next_review_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'compliance_control_assessment'
        ordering = ['-assessed_at']

    def __str__(self):
        return f'{self.control} → {self.status} ({self.assessed_at:%Y-%m-%d})'


class ComplianceEvidence(models.Model):
    """Legacy: documentary evidence supporting a control assessment."""

    assessment = models.ForeignKey(
        ControlAssessment,
        on_delete=models.CASCADE,
        related_name='evidence',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='compliance_evidence/', null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_evidence'
        verbose_name = 'Compliance Evidence'

    def __str__(self):
        return f'Evidence: {self.title} ({self.assessment.control})'


# ---------------------------------------------------------------------------
# New compliance engine models
# ---------------------------------------------------------------------------

class ComplianceControl(models.Model):
    """
    An engine-managed compliance control with automated check support.

    Each control belongs to one ComplianceFramework and defines the
    check function that ComplianceChecker will call when automated_check=True.
    The weight (0.0–1.0) determines how much this control influences the
    framework's overall compliance score.
    """

    class ControlCategory(models.TextChoices):
        ACCESS_CONTROL      = 'ACCESS_CONTROL',      'Access Control'
        AUDIT_LOGGING       = 'AUDIT_LOGGING',        'Audit Logging'
        ENCRYPTION          = 'ENCRYPTION',           'Encryption'
        INCIDENT_RESPONSE   = 'INCIDENT_RESPONSE',    'Incident Response'
        RISK_MANAGEMENT     = 'RISK_MANAGEMENT',      'Risk Management'
        PHYSICAL_SECURITY   = 'PHYSICAL_SECURITY',    'Physical Security'
        TRAINING            = 'TRAINING',             'Training & Awareness'
        DATA_BACKUP         = 'DATA_BACKUP',          'Data Backup'
        PASSWORD_POLICY     = 'PASSWORD_POLICY',      'Password Policy'
        NETWORK_SECURITY    = 'NETWORK_SECURITY',     'Network Security'

    control_id          = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    framework           = models.ForeignKey(
        ComplianceFramework,
        on_delete=models.CASCADE,
        related_name='engine_controls',
    )
    control_code        = models.CharField(max_length=80)   # e.g. "HIPAA-164.308(a)(1)"
    title               = models.CharField(max_length=300)
    description         = models.TextField()
    control_category    = models.CharField(
        max_length=25,
        choices=ControlCategory.choices,
        default=ControlCategory.ACCESS_CONTROL,
    )
    weight              = models.FloatField(
        default=1.0,
        help_text='Importance weight for scoring (0.0–1.0).',
    )
    automated_check     = models.BooleanField(
        default=False,
        help_text='Whether the system can verify this control automatically.',
    )
    check_function_name = models.CharField(
        max_length=80,
        blank=True,
        help_text='Name of the ComplianceChecker method to call.',
    )

    class Meta:
        db_table = 'compliance_engine_control'
        ordering = ['framework', 'control_code']
        unique_together = ('framework', 'control_code')

    def __str__(self):
        return f'{self.framework.short_name} — {self.control_code}: {self.title}'

    def get_latest_result(self):
        """Return the most recent ComplianceCheckResult for this control, or None."""
        return self.results.order_by('-checked_at').first()

    def get_status_badge_class(self):
        """Return a CSS badge class based on the latest check result status."""
        result = self.get_latest_result()
        if not result:
            return 'bg-secondary'
        return {
            'PASS':           'badge-low',
            'FAIL':           'badge-critical',
            'PARTIAL':        'badge-medium',
            'NOT_APPLICABLE': 'bg-secondary',
            'PENDING':        'badge-medium',
        }.get(result.status, 'bg-secondary')


class ComplianceCheckResult(models.Model):
    """
    The result of a single compliance check against a ComplianceControl.

    Results are immutable snapshots; each run of the checker creates new rows
    rather than updating existing ones so the full history is preserved.
    """

    class CheckStatus(models.TextChoices):
        PASS            = 'PASS',           'Pass'
        FAIL            = 'FAIL',           'Fail'
        PARTIAL         = 'PARTIAL',        'Partial'
        NOT_APPLICABLE  = 'NOT_APPLICABLE', 'Not Applicable'
        PENDING         = 'PENDING',        'Pending Manual Review'

    result_id           = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    control             = models.ForeignKey(
        ComplianceControl,
        on_delete=models.CASCADE,
        related_name='results',
    )
    checked_at          = models.DateTimeField(auto_now_add=True)
    checked_by          = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compliance_checks',
        help_text='Null when the check was automated.',
    )
    status              = models.CharField(
        max_length=20,
        choices=CheckStatus.choices,
        default=CheckStatus.PENDING,
    )
    score               = models.FloatField(default=0.0, help_text='0–100 score for this control.')
    notes               = models.TextField(blank=True)
    evidence            = models.TextField(blank=True, help_text='What was observed/checked.')
    remediation_steps   = models.TextField(blank=True)
    due_date            = models.DateField(null=True, blank=True, help_text='Remediation deadline.')

    class Meta:
        db_table = 'compliance_check_result'
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['control', '-checked_at']),
            models.Index(fields=['status', '-checked_at']),
        ]

    def __str__(self):
        return (
            f'{self.control.control_code} — {self.status} '
            f'({self.score:.0f}/100) @ {self.checked_at:%Y-%m-%d %H:%M}'
        )

    def get_status_badge_class(self):
        """Return a CSS badge class for the check status."""
        return {
            self.CheckStatus.PASS:           'badge-low',
            self.CheckStatus.FAIL:           'badge-critical',
            self.CheckStatus.PARTIAL:        'badge-medium',
            self.CheckStatus.NOT_APPLICABLE: 'bg-secondary',
            self.CheckStatus.PENDING:        'badge-medium',
        }.get(self.status, 'bg-secondary')


class ComplianceReport(models.Model):
    """
    A point-in-time compliance snapshot for a framework.

    Generated by running all checks and aggregating results.
    Stored for trend analysis, audit evidence, and regulatory reporting.
    """

    class ComplianceLevel(models.TextChoices):
        NON_COMPLIANT   = 'NON_COMPLIANT',   'Non-Compliant (<40%)'
        PARTIAL         = 'PARTIAL',         'Partially Compliant (40–69%)'
        COMPLIANT       = 'COMPLIANT',       'Compliant (70–89%)'
        FULLY_COMPLIANT = 'FULLY_COMPLIANT', 'Fully Compliant (≥90%)'

    report_id           = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    framework           = models.ForeignKey(
        ComplianceFramework,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    generated_at        = models.DateTimeField(auto_now_add=True)
    generated_by        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='compliance_reports',
    )
    overall_score       = models.FloatField(default=0.0)
    compliance_level    = models.CharField(
        max_length=20,
        choices=ComplianceLevel.choices,
        default=ComplianceLevel.NON_COMPLIANT,
    )
    total_controls      = models.IntegerField(default=0)
    passed_controls     = models.IntegerField(default=0)
    failed_controls     = models.IntegerField(default=0)
    summary_json        = models.JSONField(default=dict)
    pdf_report          = models.FileField(
        upload_to='compliance_reports/',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'compliance_report'
        ordering = ['-generated_at']

    def __str__(self):
        return (
            f'{self.framework.short_name} Report — '
            f'{self.compliance_level} ({self.overall_score:.1f}%) '
            f'@ {self.generated_at:%Y-%m-%d}'
        )

    def get_level_badge_class(self):
        """Return a CSS badge class for the compliance level."""
        return {
            self.ComplianceLevel.NON_COMPLIANT:   'badge-critical',
            self.ComplianceLevel.PARTIAL:         'badge-medium',
            self.ComplianceLevel.COMPLIANT:       'badge-high',
            self.ComplianceLevel.FULLY_COMPLIANT: 'badge-low',
        }.get(self.compliance_level, 'bg-secondary')

    @classmethod
    def level_from_score(cls, score: float) -> str:
        """Classify a numeric score (0-100) into a ComplianceLevel choice."""
        if score >= 90:
            return cls.ComplianceLevel.FULLY_COMPLIANT
        if score >= 70:
            return cls.ComplianceLevel.COMPLIANT
        if score >= 40:
            return cls.ComplianceLevel.PARTIAL
        return cls.ComplianceLevel.NON_COMPLIANT
