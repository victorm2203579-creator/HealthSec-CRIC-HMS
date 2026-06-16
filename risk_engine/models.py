"""
risk_engine/models.py
=====================
Models for the cyber risk intelligence engine.

Model inventory
---------------
Existing (preserved):
  RiskScore          – per-system risk score history
  Vulnerability      – CVE-backed vulnerability tracker linked to HealthcareSystem
  ThreatIntelFeed    – curated external threat intelligence entries

New (threat intelligence engine):
  ThreatEvent        – individual detected threat with severity & MITRE reference
  VulnerabilityRecord – simulated CVE-style vulnerability with patching workflow
  ThreatFeed         – IP/domain/hash IOC feed used by the engine's feed checker
  RiskAssessment     – aggregated point-in-time risk assessment snapshot
"""

import uuid

from django.db import models
from django.conf import settings
from monitoring.models import HealthcareSystem


# ---------------------------------------------------------------------------
# Existing models (unchanged)
# ---------------------------------------------------------------------------

class RiskScore(models.Model):
    """Computed risk score for a healthcare system at a specific point in time."""

    class RiskLevel(models.TextChoices):
        LOW = 'LOW', 'Low (0–3.9)'
        MEDIUM = 'MEDIUM', 'Medium (4.0–6.9)'
        HIGH = 'HIGH', 'High (7.0–8.9)'
        CRITICAL = 'CRITICAL', 'Critical (9.0–10)'

    system = models.ForeignKey(
        HealthcareSystem, on_delete=models.CASCADE, related_name='risk_scores',
    )
    score = models.DecimalField(max_digits=4, decimal_places=2)
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices)
    threat_likelihood = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    impact_magnitude = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    vulnerability_index = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    control_effectiveness = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    rationale = models.TextField(blank=True)
    calculation_inputs = models.JSONField(null=True, blank=True)
    computed_at = models.DateTimeField(auto_now_add=True)
    computed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='computed_risk_scores',
    )

    class Meta:
        db_table = 'risk_score'
        ordering = ['-computed_at']
        indexes = [models.Index(fields=['system', '-computed_at'])]

    def __str__(self):
        return f'{self.system.name}: {self.score} ({self.risk_level}) @ {self.computed_at:%Y-%m-%d}'

    @classmethod
    def classify(cls, score: float) -> str:
        """Return the RiskLevel text choice for a numeric 0-10 score."""
        if score < 4.0:
            return cls.RiskLevel.LOW
        if score < 7.0:
            return cls.RiskLevel.MEDIUM
        if score < 9.0:
            return cls.RiskLevel.HIGH
        return cls.RiskLevel.CRITICAL


class Vulnerability(models.Model):
    """Known vulnerability affecting one or more healthcare systems (CVE-backed)."""

    class VulnStatus(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'Remediation In Progress'
        MITIGATED = 'MITIGATED', 'Mitigated'
        ACCEPTED = 'ACCEPTED', 'Risk Accepted'
        RESOLVED = 'RESOLVED', 'Resolved'

    cve_id = models.CharField(max_length=20, blank=True, db_index=True)
    title = models.CharField(max_length=300)
    description = models.TextField()
    cvss_score = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    affected_systems = models.ManyToManyField(
        HealthcareSystem, related_name='vulnerabilities', blank=True,
    )
    status = models.CharField(
        max_length=20, choices=VulnStatus.choices, default=VulnStatus.OPEN,
    )
    discovered_at = models.DateField(null=True, blank=True)
    remediation_due = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_vulnerabilities',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'risk_vulnerability'
        ordering = ['-cvss_score', '-created_at']
        verbose_name = 'Vulnerability'
        verbose_name_plural = 'Vulnerabilities'

    def __str__(self):
        cve = f' [{self.cve_id}]' if self.cve_id else ''
        return f'{self.title}{cve}'


class ThreatIntelFeed(models.Model):
    """External threat intelligence feed entry (IoC, TTPs, threat actor info)."""

    class FeedType(models.TextChoices):
        IOC = 'IOC', 'Indicator of Compromise'
        TTP = 'TTP', 'Tactics, Techniques & Procedures'
        ADVISORY = 'ADVISORY', 'Security Advisory'
        ACTOR = 'ACTOR', 'Threat Actor Profile'

    feed_type = models.CharField(max_length=20, choices=FeedType.choices)
    source = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    content = models.TextField()
    relevance_score = models.PositiveSmallIntegerField(default=0)
    is_actioned = models.BooleanField(default=False)
    published_at = models.DateTimeField()
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'risk_threat_intel_feed'
        ordering = ['-published_at']

    def __str__(self):
        return f'[{self.feed_type}] {self.title} – {self.source}'


# ---------------------------------------------------------------------------
# New threat intelligence engine models
# ---------------------------------------------------------------------------

class ThreatEvent(models.Model):
    """
    An individual cyber threat event detected by the intelligence engine.

    Severity uses IntegerChoices (1–4) so events can be ordered and
    weighted arithmetically without a lookup table.
    """

    class ThreatType(models.TextChoices):
        BRUTE_FORCE          = 'BRUTE_FORCE',          'Brute Force'
        SQL_INJECTION        = 'SQL_INJECTION',        'SQL Injection'
        UNAUTHORIZED_ACCESS  = 'UNAUTHORIZED_ACCESS',  'Unauthorized Access'
        INSIDER_THREAT       = 'INSIDER_THREAT',       'Insider Threat'
        MALWARE_INDICATOR    = 'MALWARE_INDICATOR',    'Malware Indicator'
        PHISHING_ATTEMPT     = 'PHISHING_ATTEMPT',     'Phishing Attempt'
        PRIVILEGE_ESCALATION = 'PRIVILEGE_ESCALATION', 'Privilege Escalation'
        DATA_EXFILTRATION    = 'DATA_EXFILTRATION',    'Data Exfiltration'
        REPEATED_FAILURES    = 'REPEATED_FAILURES',    'Repeated Failures'
        ANOMALOUS_BEHAVIOR   = 'ANOMALOUS_BEHAVIOR',   'Anomalous Behavior'

    class Severity(models.IntegerChoices):
        LOW      = 1, 'Low'
        MEDIUM   = 2, 'Medium'
        HIGH     = 3, 'High'
        CRITICAL = 4, 'Critical'

    class Status(models.TextChoices):
        OPEN           = 'OPEN',           'Open'
        INVESTIGATING  = 'INVESTIGATING',  'Investigating'
        MITIGATED      = 'MITIGATED',      'Mitigated'
        FALSE_POSITIVE = 'FALSE_POSITIVE', 'False Positive'

    threat_id        = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    threat_type      = models.CharField(max_length=25, choices=ThreatType.choices)
    source_ip        = models.GenericIPAddressField(null=True, blank=True)
    target_user      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='targeted_threats',
    )
    target_resource  = models.CharField(max_length=255)
    severity         = models.IntegerField(choices=Severity.choices, default=Severity.MEDIUM)
    risk_score       = models.FloatField(default=0.0)
    description      = models.TextField()
    detected_at      = models.DateTimeField(auto_now_add=True)
    indicators       = models.JSONField(default=dict, blank=True)
    mitre_tactic     = models.CharField(max_length=100, blank=True)
    status           = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN,
    )
    assigned_to      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_threats',
    )

    class Meta:
        db_table = 'risk_threat_event'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['-detected_at']),
            models.Index(fields=['severity', '-detected_at']),
            models.Index(fields=['status', '-detected_at']),
            models.Index(fields=['threat_type']),
        ]

    def __str__(self):
        return f'[{self.get_severity_display()}] {self.get_threat_type_display()} – {self.detected_at:%Y-%m-%d %H:%M}'

    def get_severity_badge_class(self):
        """Return a CSS badge class for the severity level."""
        return {
            self.Severity.LOW:      'badge-low',
            self.Severity.MEDIUM:   'badge-medium',
            self.Severity.HIGH:     'badge-high',
            self.Severity.CRITICAL: 'badge-critical',
        }.get(self.severity, 'secondary')

    def get_status_badge_class(self):
        """Return a CSS badge class for the current status."""
        return {
            self.Status.OPEN:           'badge-critical',
            self.Status.INVESTIGATING:  'badge-medium',
            self.Status.MITIGATED:      'badge-low',
            self.Status.FALSE_POSITIVE: 'bg-secondary',
        }.get(self.status, 'secondary')


class VulnerabilityRecord(models.Model):
    """
    A simulated CVE-style vulnerability entry with a full patching workflow.

    Separate from the legacy Vulnerability model which is linked to
    HealthcareSystem objects and used by RiskScoringService.
    """

    class Severity(models.TextChoices):
        NONE     = 'NONE',     'None'
        LOW      = 'LOW',      'Low'
        MEDIUM   = 'MEDIUM',   'Medium'
        HIGH     = 'HIGH',     'High'
        CRITICAL = 'CRITICAL', 'Critical'

    vuln_id            = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title              = models.CharField(max_length=300)
    description        = models.TextField()
    cve_reference      = models.CharField(max_length=30, blank=True)
    cvss_score         = models.FloatField(default=0.0)
    severity           = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.MEDIUM,
    )
    affected_component = models.CharField(max_length=200)
    discovered_at      = models.DateTimeField()
    patched            = models.BooleanField(default=False, db_index=True)
    patched_at         = models.DateTimeField(null=True, blank=True)
    patch_notes        = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'risk_vulnerability_record'
        ordering = ['-cvss_score', '-discovered_at']
        indexes = [
            models.Index(fields=['patched', '-discovered_at']),
            models.Index(fields=['severity']),
        ]

    def __str__(self):
        ref = f' ({self.cve_reference})' if self.cve_reference else ''
        return f'{self.title}{ref} — CVSS {self.cvss_score:.1f}'

    def get_severity_badge_class(self):
        """Return a CSS badge class for the severity level."""
        return {
            self.Severity.NONE:     'bg-secondary',
            self.Severity.LOW:      'badge-low',
            self.Severity.MEDIUM:   'badge-medium',
            self.Severity.HIGH:     'badge-high',
            self.Severity.CRITICAL: 'badge-critical',
        }.get(self.severity, 'secondary')

    def cvss_bar_width(self):
        """Return the CVSS score as a percentage string for progress bars."""
        return f'{min(self.cvss_score / 10.0 * 100, 100):.0f}%'


class ThreatFeed(models.Model):
    """
    Simulated threat intelligence IOC feed entry.

    Used by RiskIntelligenceEngine.check_threat_feed() to flag known-bad
    IP addresses, domains, file hashes, and behavioural patterns.
    """

    class IndicatorType(models.TextChoices):
        IP        = 'IP',        'IP Address'
        DOMAIN    = 'DOMAIN',    'Domain'
        HASH      = 'HASH',      'File Hash'
        PATTERN   = 'PATTERN',   'Behaviour Pattern'
        SIGNATURE = 'SIGNATURE', 'Attack Signature'

    feed_name         = models.CharField(max_length=100)
    threat_indicator  = models.CharField(max_length=500, db_index=True)
    indicator_type    = models.CharField(max_length=15, choices=IndicatorType.choices)
    threat_category   = models.CharField(max_length=100)
    confidence_score  = models.FloatField(default=0.0)
    added_at          = models.DateTimeField()
    is_active         = models.BooleanField(default=True, db_index=True)
    source            = models.CharField(max_length=100)

    class Meta:
        db_table = 'risk_threat_feed'
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['indicator_type', 'is_active']),
            models.Index(fields=['confidence_score']),
        ]

    def __str__(self):
        return f'[{self.indicator_type}] {self.threat_indicator} — {self.feed_name}'


class RiskAssessment(models.Model):
    """
    An aggregated point-in-time risk assessment snapshot.

    Generated by RiskIntelligenceEngine.generate_risk_assessment() and
    stored for historical trending and compliance evidence.
    """

    class RiskLevel(models.TextChoices):
        LOW      = 'LOW',      'Low'
        MEDIUM   = 'MEDIUM',   'Medium'
        HIGH     = 'HIGH',     'High'
        CRITICAL = 'CRITICAL', 'Critical'

    assessment_id           = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    conducted_by            = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='risk_assessments',
    )
    conducted_at            = models.DateTimeField(auto_now_add=True)
    overall_risk_score      = models.FloatField(default=0.0)
    risk_level              = models.CharField(
        max_length=10, choices=RiskLevel.choices, default=RiskLevel.LOW,
    )
    threat_count_by_severity = models.JSONField(default=dict)
    top_threats              = models.JSONField(default=list)
    recommendations         = models.TextField(blank=True)
    next_assessment_due     = models.DateField()

    class Meta:
        db_table = 'risk_assessment'
        ordering = ['-conducted_at']

    def __str__(self):
        return (
            f'Assessment {self.assessment_id} — '
            f'{self.risk_level} ({self.overall_risk_score:.1f}) '
            f'@ {self.conducted_at:%Y-%m-%d}'
        )

    def get_risk_level_badge_class(self):
        """Return a CSS badge class for the overall risk level."""
        return {
            self.RiskLevel.LOW:      'badge-low',
            self.RiskLevel.MEDIUM:   'badge-medium',
            self.RiskLevel.HIGH:     'badge-high',
            self.RiskLevel.CRITICAL: 'badge-critical',
        }.get(self.risk_level, 'secondary')
