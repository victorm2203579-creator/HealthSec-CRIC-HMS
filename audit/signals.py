"""
audit/signals.py
================
Django signals to automatically log significant events from all modules.

Connects to post_save, post_delete, and custom signals to create audit log
entries when important actions occur in other apps.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .services import AuditService
from .models import AuditLog

User = get_user_model()


# ============================================================================
# Accounts Module Signals
# ============================================================================

@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user creation and profile updates."""
    if created:
        AuditService.log(
            user=None,
            action_category=AuditLog.ActionCategory.USER_MANAGEMENT,
            action='USER_CREATED',
            description=f'User account created: {instance.username}',
            target_model='User',
            target_id=str(instance.id),
            new_value={
                'username': instance.username,
                'email': instance.email,
                'is_staff': instance.is_staff,
                'is_superuser': instance.is_superuser,
            },
            status=AuditLog.Status.SUCCESS,
        )


# ============================================================================
# Monitoring Module Signals
# ============================================================================

def log_monitoring_event(sender, instance, created, **kwargs):
    """
    Log when monitoring events are created.

    This is called from monitoring.signals.
    """
    if created:
        severity_map = {
            'INFO': AuditLog.ActionCategory.SYSTEM,
            'LOW': AuditLog.ActionCategory.DATA_ACCESS,
            'MEDIUM': AuditLog.ActionCategory.DATA_ACCESS,
            'HIGH': AuditLog.ActionCategory.DATA_ACCESS,
            'CRITICAL': AuditLog.ActionCategory.DATA_ACCESS,
        }

        category = severity_map.get(instance.severity, AuditLog.ActionCategory.DATA_ACCESS)

        AuditService.log(
            user=instance.reviewed_by if hasattr(instance, 'reviewed_by') else None,
            action_category=category,
            action='MONITORING_EVENT',
            description=f'Monitoring event recorded: {instance.title}',
            target_model='MonitoringEvent',
            target_id=str(instance.id),
            new_value={
                'event_type': instance.event_type,
                'severity': instance.severity,
                'title': instance.title,
            },
            status=AuditLog.Status.SUCCESS,
        )


def log_suspicious_activity(sender, instance, created, **kwargs):
    """
    Log when suspicious activity is flagged.

    This is called from monitoring.signals.
    """
    if created:
        AuditService.log(
            user=None,
            action_category=AuditLog.ActionCategory.DATA_ACCESS,
            action='SUSPICIOUS_ACTIVITY',
            description=f'Suspicious activity detected: {instance.get_activity_type_display()}',
            target_model='SuspiciousActivity',
            target_id=str(instance.activity_id),
            new_value={
                'activity_type': instance.activity_type,
                'severity': instance.severity,
                'user': instance.user.username if instance.user else 'Unknown',
            },
            status=AuditLog.Status.SUCCESS,
        )


# ============================================================================
# Risk Engine Module Signals
# ============================================================================

def log_risk_score(sender, instance, created, **kwargs):
    """
    Log when risk scores are computed.

    This is called from risk_engine.signals.
    """
    if created:
        AuditService.log(
            user=None,
            action_category=AuditLog.ActionCategory.DATA_MODIFICATION,
            action='RISK_SCORE_COMPUTED',
            description=f'Risk score computed: {instance.overall_score:.1f}',
            target_model='RiskScore',
            target_id=str(instance.id),
            new_value={
                'overall_score': instance.overall_score,
                'framework': str(instance.framework) if hasattr(instance, 'framework') else None,
            },
            status=AuditLog.Status.SUCCESS,
        )


# ============================================================================
# Compliance Module Signals
# ============================================================================

def log_compliance_check(sender, instance, created, **kwargs):
    """
    Log when compliance checks are run.

    This is called from compliance.signals.
    """
    if created:
        AuditService.log(
            user=instance.checked_by if hasattr(instance, 'checked_by') else None,
            action_category=AuditLog.ActionCategory.COMPLIANCE,
            action='COMPLIANCE_CHECK',
            description=f'Compliance check completed',
            target_model='ComplianceCheckResult',
            target_id=str(instance.id),
            new_value={
                'framework': str(instance.framework) if hasattr(instance, 'framework') else None,
                'passed': instance.passed if hasattr(instance, 'passed') else None,
            },
            status=AuditLog.Status.SUCCESS,
        )


# ============================================================================
# Alerts Module Signals
# ============================================================================

def log_alert_created(sender, instance, created, **kwargs):
    """
    Log when alerts are created.

    This is called from alerts.signals.
    """
    if created:
        AuditService.log(
            user=None,
            action_category=AuditLog.ActionCategory.ALERT,
            action='ALERT_CREATED',
            description=f'Alert created: {instance.title}',
            target_model='Alert',
            target_id=str(instance.id),
            new_value={
                'alert_type': instance.alert_type,
                'severity': instance.severity,
                'status': instance.status,
            },
            status=AuditLog.Status.SUCCESS,
        )


def log_alert_resolved(sender, instance, created, **kwargs):
    """
    Log when alerts are resolved.

    This is called from alerts.signals when alert status changes.
    """
    if instance.status in ['RESOLVED', 'CLOSED', 'FP']:
        AuditService.log(
            user=instance.resolved_by if hasattr(instance, 'resolved_by') else None,
            action_category=AuditLog.ActionCategory.ALERT,
            action='ALERT_RESOLVED',
            description=f'Alert resolved: {instance.title}',
            target_model='Alert',
            target_id=str(instance.id),
            new_value={
                'status': instance.status,
                'resolved_at': instance.resolved_at.isoformat() if instance.resolved_at else None,
            },
            status=AuditLog.Status.SUCCESS,
        )


def log_incident_created(sender, instance, created, **kwargs):
    """
    Log when incidents are created.

    This is called from alerts.signals.
    """
    if created:
        AuditService.log(
            user=instance.created_by if hasattr(instance, 'created_by') else None,
            action_category=AuditLog.ActionCategory.ALERT,
            action='INCIDENT_CREATED',
            description=f'Incident created: {instance.incident_number}',
            target_model='Incident',
            target_id=str(instance.id),
            new_value={
                'incident_number': instance.incident_number,
                'title': instance.title,
                'phase': instance.phase,
            },
            status=AuditLog.Status.SUCCESS,
        )


def ready():
    """Signal handlers are registered in audit/apps.py ready() method."""
    pass
