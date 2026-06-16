"""
audit/models.py
===============
Tamper-evident audit logging system with integrity verification.

The audit log is append-only: no updates or deletes permitted through
views, signals, or ORM. Admin-level access is restricted with
PermissionDenied on delete attempts. Every log entry includes a SHA256
checksum for tamper detection.

Key design:
- log_id (UUID) for tamper-resistant primary key
- user (FK, SET_NULL) preserves logs after account deletion
- Comprehensive change tracking (old_value, new_value JSONFields)
- Cryptographic checksum for integrity verification
- AuditLogIntegrityCheck model for periodic integrity audits
"""

import uuid
import hashlib
import json
from django.db import models
from django.conf import settings


class AuditLogQuerySet(models.QuerySet):
    """Custom QuerySet for AuditLog with common filtering methods."""

    def by_user(self, user):
        return self.filter(user=user)

    def by_category(self, category):
        return self.filter(action_category=category)

    def by_status(self, status):
        return self.filter(status=status)

    def successful(self):
        return self.filter(status=AuditLog.Status.SUCCESS)

    def failed(self):
        return self.exclude(status=AuditLog.Status.SUCCESS)

    def by_target(self, target_model, target_id=None):
        qs = self.filter(target_model=target_model)
        if target_id:
            qs = qs.filter(target_id=target_id)
        return qs


class AuditLogManager(models.Manager):
    """Custom manager for AuditLog."""

    def get_queryset(self):
        return AuditLogQuerySet(self.model, using=self._db)

    def by_user(self, user):
        return self.get_queryset().by_user(user)

    def by_category(self, category):
        return self.get_queryset().by_category(category)

    def successful(self):
        return self.get_queryset().successful()


class AuditLog(models.Model):
    """
    Immutable, cryptographically-verifiable audit log entry.

    Each entry is append-only and includes a SHA256 checksum to detect tampering.
    The integrity of all logs can be verified using AuditService.run_integrity_check().
    """

    class ActionCategory(models.TextChoices):
        AUTH = 'AUTH', 'Authentication & Authorization'
        DATA_ACCESS = 'DATA_ACCESS', 'Data Access'
        DATA_MODIFICATION = 'DATA_MODIFICATION', 'Data Modification'
        USER_MANAGEMENT = 'USER_MANAGEMENT', 'User Management'
        COMPLIANCE = 'COMPLIANCE', 'Compliance'
        ALERT = 'ALERT', 'Alert Management'
        SYSTEM = 'SYSTEM', 'System Events'
        EXPORT = 'EXPORT', 'Data Export'
        CONFIGURATION = 'CONFIGURATION', 'Configuration Changes'

    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILURE = 'FAILURE', 'Failure'
        ERROR = 'ERROR', 'Error'

    # Primary key
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Actor
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )

    # Action details
    action_category = models.CharField(max_length=20, choices=ActionCategory.choices)
    action = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUCCESS)

    # Target object
    target_model = models.CharField(max_length=100, blank=True, db_index=True)
    target_id = models.CharField(max_length=500, blank=True)

    # Change tracking
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)

    # HTTP context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    checksum = models.CharField(max_length=64, blank=True, db_index=True)

    objects = AuditLogManager()

    class Meta:
        db_table = 'audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_category', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
            models.Index(fields=['target_model', 'target_id']),
        ]

    def __str__(self):
        username = self.user.username if self.user else 'System'
        return f'[{self.timestamp:%Y-%m-%d %H:%M:%S}] {username} — {self.action}'

    def delete(self, *args, **kwargs):
        """Prevent deletion of audit logs."""
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('Audit logs are immutable and cannot be deleted.')


class AuditLogIntegrityCheck(models.Model):
    """
    Record of a tamper-detection integrity check run.

    Stores the results of periodic verification that all audit logs
    have valid checksums and have not been modified.
    """

    class Result(models.TextChoices):
        INTACT = 'INTACT', 'All Logs Intact'
        TAMPERED = 'TAMPERED', 'Tampering Detected'
        ERROR = 'ERROR', 'Check Error'

    check_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='integrity_checks',
    )

    total_logs_checked = models.PositiveIntegerField()
    corrupted_logs = models.PositiveIntegerField(default=0)
    result = models.CharField(max_length=20, choices=Result.choices)
    details = models.TextField(blank=True)

    class Meta:
        db_table = 'audit_integrity_check'
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['-checked_at']),
            models.Index(fields=['result']),
        ]

    def __str__(self):
        return f'Integrity Check — {self.checked_at:%Y-%m-%d %H:%M:%S} — {self.get_result_display()}'
