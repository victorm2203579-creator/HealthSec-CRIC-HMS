"""
alerts/signals.py
================
Signal handlers for automatic alert generation from monitoring events,
suspicious activity, and security incidents.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from monitoring.models import MonitoringEvent, SuspiciousActivity
from .models import Alert
from .services import AlertService


@receiver(post_save, sender=MonitoringEvent)
def create_alert_from_monitoring_event(sender, instance, created, **kwargs):
    """
    Create an alert when a high-severity monitoring event is created.

    Filters based on event severity – only CRITICAL, HIGH, and MEDIUM events
    trigger automatic alerts.
    """
    if not created:
        return

    event = instance
    severity_mapping = {
        MonitoringEvent.Severity.CRITICAL: Alert.Severity.CRITICAL,
        MonitoringEvent.Severity.HIGH: Alert.Severity.HIGH,
        MonitoringEvent.Severity.MEDIUM: Alert.Severity.MEDIUM,
        MonitoringEvent.Severity.LOW: Alert.Severity.LOW,
    }

    alert_type_mapping = {
        MonitoringEvent.EventType.SECURITY: Alert.AlertType.SECURITY,
        MonitoringEvent.EventType.COMPLIANCE: Alert.AlertType.COMPLIANCE,
        MonitoringEvent.EventType.PERFORMANCE: Alert.AlertType.PERFORMANCE,
        MonitoringEvent.EventType.AVAILABILITY: Alert.AlertType.AVAILABILITY,
        MonitoringEvent.EventType.DATA_ACCESS: Alert.AlertType.SUSPICIOUS_ACTIVITY,
        MonitoringEvent.EventType.CONFIGURATION: Alert.AlertType.POLICY,
    }

    if event.severity in [MonitoringEvent.Severity.CRITICAL, MonitoringEvent.Severity.HIGH]:
        alert_severity = severity_mapping.get(event.severity, Alert.Severity.MEDIUM)
        alert_type = alert_type_mapping.get(event.event_type, Alert.AlertType.SECURITY)

        alert = AlertService.create_alert(
            title=f"Monitoring: {event.title}",
            description=event.description,
            alert_type=alert_type,
            severity=alert_severity,
            affected_system=event.system,
            source_event=event,
            tags="auto-generated,monitoring"
        )

        AlertService.notify_stakeholders(alert, 'created')


@receiver(post_save, sender=SuspiciousActivity)
def create_alert_from_suspicious_activity(sender, instance, created, **kwargs):
    """
    Create an alert when suspicious activity is flagged.

    Filters based on activity severity – HIGH and CRITICAL activities
    trigger alerts automatically, MEDIUM activities are created but not escalated.
    """
    if not created:
        return

    activity = instance
    severity_mapping = {
        SuspiciousActivity.Severity.CRITICAL: Alert.Severity.CRITICAL,
        SuspiciousActivity.Severity.HIGH: Alert.Severity.HIGH,
        SuspiciousActivity.Severity.MEDIUM: Alert.Severity.MEDIUM,
        SuspiciousActivity.Severity.LOW: Alert.Severity.LOW,
    }

    alert_severity = severity_mapping.get(activity.severity, Alert.Severity.MEDIUM)

    alert = AlertService.create_alert(
        title=f"Suspicious Activity: {activity.get_activity_type_display()}",
        description=f"User: {activity.user.username if activity.user else 'Unknown'}\n\n{activity.description}",
        alert_type=Alert.AlertType.SUSPICIOUS_ACTIVITY,
        severity=alert_severity,
        tags="auto-generated,suspicious-activity"
    )

    if activity.severity in [SuspiciousActivity.Severity.CRITICAL, SuspiciousActivity.Severity.HIGH]:
        AlertService.notify_stakeholders(alert, 'created')


def ready():
    """Called when the app is ready. Register signal handlers."""
    pass
