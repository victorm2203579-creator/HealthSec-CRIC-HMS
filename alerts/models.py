"""
alerts/models.py
================
Models for the alert and incident response subsystem.

Alert lifecycle:
  NEW → ACKNOWLEDGED → IN_PROGRESS → RESOLVED | CLOSED | FALSE_POSITIVE

Incidents are created from one or more related alerts for formal response tracking.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from monitoring.models import HealthcareSystem, MonitoringEvent
import uuid


class AlertQuerySet(models.QuerySet):
    def unread(self):
        return self.filter(is_read=False)

    def by_severity(self, severity):
        return self.filter(severity=severity)

    def by_status(self, status):
        return self.filter(status=status)

    def assigned_to(self, user):
        return self.filter(assigned_to=user)

    def unassigned(self):
        return self.filter(assigned_to__isnull=True)

    def open(self):
        return self.exclude(status__in=[Alert.Status.RESOLVED, Alert.Status.CLOSED, Alert.Status.FALSE_POSITIVE])


class AlertManager(models.Manager):
    def get_queryset(self):
        return AlertQuerySet(self.model, using=self._db)

    def unread(self):
        return self.get_queryset().unread()

    def by_severity(self, severity):
        return self.get_queryset().by_severity(severity)

    def open(self):
        return self.get_queryset().open()


class Alert(models.Model):
    """A security or compliance alert raised by the monitoring or risk engine."""

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        ACKNOWLEDGED = 'ACK', 'Acknowledged'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
        FALSE_POSITIVE = 'FP', 'False Positive'

    class AlertType(models.TextChoices):
        SECURITY = 'SECURITY', 'Security Issue'
        COMPLIANCE = 'COMPLIANCE', 'Compliance Violation'
        PERFORMANCE = 'PERFORMANCE', 'Performance Degradation'
        AVAILABILITY = 'AVAILABILITY', 'Availability Issue'
        DATA_BREACH = 'DATA_BREACH', 'Data Breach Risk'
        POLICY = 'POLICY', 'Policy Violation'
        UNAUTHORIZED_ACCESS = 'UNAUTH_ACCESS', 'Unauthorized Access'
        PRIVILEGE_ESCALATION = 'PRIV_ESCALATION', 'Privilege Escalation'
        SUSPICIOUS_ACTIVITY = 'SUSPICIOUS', 'Suspicious Activity'
        AUDIT_ANOMALY = 'AUDIT_ANOMALY', 'Audit Anomaly'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    description = models.TextField()
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    affected_system = models.ForeignKey(
        HealthcareSystem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
    )

    source_event = models.ForeignKey(
        MonitoringEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_alerts',
    )

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
    )

    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags for filtering")

    objects = AlertManager()

    class Meta:
        db_table = 'alerts_alert'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f'[{self.severity}] {self.title}'

    def mark_as_read(self, user=None):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])

    def acknowledge(self, user):
        self.status = self.Status.ACKNOWLEDGED
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save(update_fields=['status', 'acknowledged_at', 'acknowledged_by'])

    def resolve(self, user, new_status=Status.RESOLVED):
        self.status = new_status
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save(update_fields=['status', 'resolved_at', 'resolved_by'])


class IncidentQuerySet(models.QuerySet):
    def open(self):
        return self.exclude(phase=Incident.Phase.CLOSED)

    def by_phase(self, phase):
        return self.filter(phase=phase)


class IncidentManager(models.Manager):
    def get_queryset(self):
        return IncidentQuerySet(self.model, using=self._db)

    def open(self):
        return self.get_queryset().open()

    def get_next_incident_number(self):
        from django.db.models import Max, F
        from datetime import datetime
        year = datetime.now().year
        latest = self.filter(incident_number__startswith=f'INC-{year}').aggregate(
            max_seq=Max('incident_sequence')
        )
        seq = (latest['max_seq'] or 0) + 1
        return f'INC-{year}-{seq:04d}', seq


class Incident(models.Model):
    """A formal security incident created from one or more alerts. Follows NIST IR lifecycle."""

    class Phase(models.TextChoices):
        PREPARATION = 'PREP', 'Preparation'
        DETECTION = 'DETECT', 'Detection & Analysis'
        CONTAINMENT = 'CONTAIN', 'Containment'
        ERADICATION = 'ERADICATE', 'Eradication'
        RECOVERY = 'RECOVER', 'Recovery'
        POST_INCIDENT = 'POST', 'Post-Incident Activity'
        CLOSED = 'CLOSED', 'Closed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_number = models.CharField(max_length=20, unique=True, db_index=True, null=True, blank=True)
    incident_sequence = models.PositiveIntegerField(db_index=True, null=True, blank=True)

    title = models.CharField(max_length=300)
    description = models.TextField()
    phase = models.CharField(max_length=20, choices=Phase.choices, default=Phase.DETECTION)

    alerts = models.ManyToManyField(Alert, related_name='incidents', blank=True)

    incident_commander = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commanded_incidents',
    )

    detected_at = models.DateTimeField()
    contained_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    impact_assessment = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    remediation_steps = models.TextField(blank=True)

    timeline = models.JSONField(default=list, blank=True, help_text="Chronological event log")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_incidents',
    )

    objects = IncidentManager()

    class Meta:
        db_table = 'alerts_incident'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['incident_number']),
            models.Index(fields=['phase', '-detected_at']),
        ]

    def __str__(self):
        return f'{self.incident_number}: {self.title}'

    def save(self, *args, **kwargs):
        if not self.incident_number:
            self.incident_number, self.incident_sequence = Incident.objects.get_next_incident_number()
        super().save(*args, **kwargs)

    def add_timeline_entry(self, action, user, details=""):
        entry = {
            'timestamp': timezone.now().isoformat(),
            'action': action,
            'user': user.username if user else 'System',
            'details': details
        }
        timeline = self.timeline or []
        timeline.append(entry)
        self.timeline = timeline
        self.save(update_fields=['timeline'])

    def transition_phase(self, new_phase, user, notes=""):
        self.phase = new_phase
        if new_phase == self.Phase.CLOSED:
            self.closed_at = timezone.now()
        self.add_timeline_entry(f'Phase changed to {new_phase}', user, notes)
        self.save(update_fields=['phase', 'closed_at'])


class AlertRule(models.Model):
    """Rule for automated alert generation based on conditions."""

    class RuleType(models.TextChoices):
        THRESHOLD = 'THRESHOLD', 'Threshold-based'
        PATTERN = 'PATTERN', 'Pattern-based'
        RULE_ENGINE = 'RULE_ENGINE', 'Rule Engine'
        MANUAL = 'MANUAL', 'Manual Review'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    rule_type = models.CharField(max_length=20, choices=RuleType.choices)
    is_active = models.BooleanField(default=True)

    alert_type = models.CharField(max_length=20, choices=Alert.AlertType.choices)
    severity = models.CharField(max_length=10, choices=Alert.Severity.choices)

    conditions = models.JSONField(default=dict, help_text="Rule conditions as JSON")
    actions = models.JSONField(default=dict, help_text="Actions to take when rule matches")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_rules',
    )

    class Meta:
        db_table = 'alerts_alert_rule'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'rule_type']),
        ]

    def __str__(self):
        return f'{self.name} ({self.rule_type})'
