"""
monitoring/models.py
====================
Models for healthcare information monitoring.

Tracks healthcare systems, data assets, monitoring events, and the
patient-record access monitoring subsystem (PatientRecord,
RecordAccessLog, SuspiciousActivity).
"""

import uuid

from django.db import models
from django.conf import settings


# ---------------------------------------------------------------------------
# Existing infrastructure models (HealthcareSystem, MonitoringEvent, DataAsset)
# ---------------------------------------------------------------------------

class HealthcareSystem(models.Model):
    """Represents a monitored healthcare system or application."""

    class SystemType(models.TextChoices):
        EHR = 'EHR', 'Electronic Health Record'
        LIS = 'LIS', 'Laboratory Information System'
        PACS = 'PACS', 'Picture Archiving & Communication System'
        HIS = 'HIS', 'Hospital Information System'
        PHARMACY = 'PHARMACY', 'Pharmacy System'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        DEGRADED = 'DEGRADED', 'Degraded'
        OFFLINE = 'OFFLINE', 'Offline'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'

    name = models.CharField(max_length=200)
    system_type = models.CharField(max_length=20, choices=SystemType.choices, default=SystemType.OTHER)
    description = models.TextField(blank=True)
    vendor = models.CharField(max_length=100, blank=True)
    version = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    hostname = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    contains_phi = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_systems',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'monitoring_healthcare_system'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_system_type_display()})'


class MonitoringEvent(models.Model):
    """
    A single monitoring event captured from a healthcare system.

    Events can be security incidents, performance issues, or configuration
    changes – the severity field guides alert generation.
    """

    class Severity(models.TextChoices):
        INFO = 'INFO', 'Informational'
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class EventType(models.TextChoices):
        SECURITY = 'SECURITY', 'Security Incident'
        PERFORMANCE = 'PERFORMANCE', 'Performance Issue'
        AVAILABILITY = 'AVAILABILITY', 'Availability Issue'
        COMPLIANCE = 'COMPLIANCE', 'Compliance Violation'
        CONFIGURATION = 'CONFIG', 'Configuration Change'
        DATA_ACCESS = 'DATA_ACCESS', 'Data Access Anomaly'

    system = models.ForeignKey(
        HealthcareSystem,
        on_delete=models.CASCADE,
        related_name='events',
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.INFO)
    title = models.CharField(max_length=300)
    description = models.TextField()
    raw_data = models.JSONField(null=True, blank=True)
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_events',
    )
    occurred_at = models.DateTimeField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monitoring_event'
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['-occurred_at']),
            models.Index(fields=['severity', '-occurred_at']),
        ]

    def __str__(self):
        return f'[{self.severity}] {self.title} @ {self.system.name}'


class DataAsset(models.Model):
    """
    A data asset held by a healthcare system (e.g. patient records database).
    Used by the risk engine to assess data exposure impact.
    """

    class DataClassification(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        INTERNAL = 'INTERNAL', 'Internal'
        CONFIDENTIAL = 'CONFIDENTIAL', 'Confidential'
        PHI = 'PHI', 'Protected Health Information'
        PII = 'PII', 'Personally Identifiable Information'

    system = models.ForeignKey(HealthcareSystem, on_delete=models.CASCADE, related_name='data_assets')
    name = models.CharField(max_length=200)
    classification = models.CharField(
        max_length=20,
        choices=DataClassification.choices,
        default=DataClassification.INTERNAL,
    )
    description = models.TextField(blank=True)
    record_count = models.PositiveBigIntegerField(default=0)
    encrypted_at_rest = models.BooleanField(default=False)
    encrypted_in_transit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monitoring_data_asset'

    def __str__(self):
        return f'{self.name} [{self.classification}]'


# ---------------------------------------------------------------------------
# Patient-record access monitoring subsystem
# ---------------------------------------------------------------------------

class PatientRecord(models.Model):
    """
    Simulated patient record used to demonstrate PHI access monitoring.

    No real patient data is stored. patient_code is a synthetic identifier
    (e.g. 'PAT-00142') and all fields are fabricated for demo purposes.
    """

    class RecordType(models.TextChoices):
        MEDICAL_HISTORY = 'MEDICAL_HISTORY', 'Medical History'
        PRESCRIPTION = 'PRESCRIPTION', 'Prescription'
        LAB_RESULT = 'LAB_RESULT', 'Lab Result'
        INSURANCE = 'INSURANCE', 'Insurance'
        IMAGING = 'IMAGING', 'Imaging'
        PERSONAL_INFO = 'PERSONAL_INFO', 'Personal Info'

    class SensitivityLevel(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    record_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    patient_code = models.CharField(max_length=20, db_index=True)
    record_type = models.CharField(max_length=20, choices=RecordType.choices)
    sensitivity_level = models.CharField(
        max_length=10,
        choices=SensitivityLevel.choices,
        default=SensitivityLevel.MEDIUM,
    )
    department = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_records',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    is_flagged = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'monitoring_patient_record'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sensitivity_level', '-created_at']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f'{self.patient_code} – {self.get_record_type_display()} [{self.sensitivity_level}]'

    def get_sensitivity_badge_class(self):
        """Return a Bootstrap badge CSS class for this record's sensitivity."""
        return {
            self.SensitivityLevel.LOW: 'badge-low',
            self.SensitivityLevel.MEDIUM: 'badge-medium',
            self.SensitivityLevel.HIGH: 'badge-high',
            self.SensitivityLevel.CRITICAL: 'badge-critical',
        }.get(self.sensitivity_level, 'secondary')


class RecordAccessLog(models.Model):
    """
    Immutable log of every access to a patient record.

    Created by the PatientRecord views whenever a user views, edits,
    downloads, prints, deletes, or shares a record.  The MonitoringEngine
    analyses each new entry and sets is_suspicious / suspicion_reason.
    """

    class AccessType(models.TextChoices):
        VIEW = 'VIEW', 'View'
        EDIT = 'EDIT', 'Edit'
        DOWNLOAD = 'DOWNLOAD', 'Download'
        PRINT = 'PRINT', 'Print'
        DELETE = 'DELETE', 'Delete'
        SHARE = 'SHARE', 'Share'

    log_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='access_logs',
    )
    patient_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name='access_logs',
    )
    access_type = models.CharField(max_length=10, choices=AccessType.choices, default=AccessType.VIEW)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255, blank=True)
    access_hour = models.IntegerField(default=0)
    is_suspicious = models.BooleanField(default=False, db_index=True)
    suspicion_reason = models.CharField(max_length=500, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)

    class Meta:
        db_table = 'monitoring_record_access_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['is_suspicious', '-timestamp']),
        ]

    def __str__(self):
        return (
            f'{self.user} {self.access_type} '
            f'{self.patient_record.patient_code} @ {self.timestamp:%Y-%m-%d %H:%M}'
        )


class SuspiciousActivity(models.Model):
    """
    A flagged anomalous access event requiring analyst review.

    Created automatically by MonitoringEngine.flag_suspicious_activity()
    whenever a RecordAccessLog scores >= 40 on the suspicion scale.
    """

    class ActivityType(models.TextChoices):
        AFTER_HOURS_ACCESS = 'AFTER_HOURS', 'After-Hours Access'
        BULK_DOWNLOAD = 'BULK_DOWNLOAD', 'Bulk Download'
        UNAUTHORIZED_ATTEMPT = 'UNAUTHORIZED', 'Unauthorized Attempt'
        PRIVILEGE_ESCALATION = 'PRIV_ESC', 'Privilege Escalation'
        REPEATED_FAILED_ACCESS = 'REPEATED_FAIL', 'Repeated Failed Access'
        UNUSUAL_VOLUME = 'UNUSUAL_VOL', 'Unusual Volume'
        CROSS_DEPARTMENT_ACCESS = 'CROSS_DEPT', 'Cross-Department Access'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    activity_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='suspicious_activities',
    )
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    related_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suspicious_activities',
    )
    resolved = models.BooleanField(default=False, db_index=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_activities',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'monitoring_suspicious_activity'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['resolved', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
        ]

    def __str__(self):
        return f'[{self.severity}] {self.get_activity_type_display()} – {self.user}'

    def get_severity_badge_class(self):
        """Return a Bootstrap badge CSS class for this activity's severity."""
        return {
            self.Severity.LOW: 'badge-low',
            self.Severity.MEDIUM: 'badge-medium',
            self.Severity.HIGH: 'badge-high',
            self.Severity.CRITICAL: 'badge-critical',
        }.get(self.severity, 'secondary')
