"""
alerts/services.py
==================
Business logic layer for alert and incident management.
"""

from django.db import transaction
from django.core.mail import send_mass_mail
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import logging

from .models import Alert, Incident, AlertRule
from .email_service import EmailNotificationService
from audit.utils import log_event
from audit.models import AuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


class AlertService:
    """Service layer for alert lifecycle management."""

    @staticmethod
    @transaction.atomic
    def create_alert(title, description, alert_type, severity, affected_system=None,
                     source_event=None, tags=""):
        """
        Create a new alert with audit logging.

        Returns:
            Alert instance
        """
        alert = Alert.objects.create(
            title=title,
            description=description,
            alert_type=alert_type,
            severity=severity,
            affected_system=affected_system,
            source_event=source_event,
            tags=tags,
            status=Alert.Status.NEW
        )
        log_event(
            action='ALERT_CREATED',
            description=f'Alert created: {title}',
            action_category=AuditLog.ActionCategory.ALERT,
            target_model='Alert',
            target_id=str(alert.id)
        )
        return alert

    @staticmethod
    @transaction.atomic
    def acknowledge_alert(alert, user, notes=""):
        """
        Acknowledge an alert and assign to user.

        Args:
            alert: Alert instance
            user: User instance
            notes: Optional acknowledgement notes
        """
        alert.acknowledge(user)
        alert.assigned_to = user
        alert.save(update_fields=['assigned_to'])

        log_event(
            action='ALERT_ACKNOWLEDGED',
            description=f'Alert acknowledged by {user.username}',
            user=user,
            action_category=AuditLog.ActionCategory.ALERT,
            target_model='Alert',
            target_id=str(alert.id)
        )

        return alert

    @staticmethod
    @transaction.atomic
    def resolve_alert(alert, user, resolution_status=Alert.Status.RESOLVED, notes=""):
        """
        Resolve an alert.

        Args:
            alert: Alert instance
            user: User instance
            resolution_status: Status to set (RESOLVED, CLOSED, or FALSE_POSITIVE)
            notes: Resolution notes
        """
        alert.resolve(user, resolution_status)

        log_event(
            action='ALERT_RESOLVED',
            description=f'Alert resolved as {resolution_status}. Notes: {notes}',
            user=user,
            action_category=AuditLog.ActionCategory.ALERT,
            target_model='Alert',
            target_id=str(alert.id)
        )

        return alert

    @staticmethod
    @transaction.atomic
    def create_incident(title, description, alerts=None, detected_at=None, incident_commander=None, created_by=None):
        """
        Create a new incident from related alerts.

        Args:
            title: Incident title
            description: Incident description
            alerts: QuerySet or list of Alert instances
            detected_at: Detection timestamp (defaults to now)
            incident_commander: User instance to assign as commander
            created_by: User instance who created the incident

        Returns:
            Incident instance
        """
        if detected_at is None:
            detected_at = timezone.now()

        incident = Incident.objects.create(
            title=title,
            description=description,
            detected_at=detected_at,
            incident_commander=incident_commander,
            created_by=created_by,
            phase=Incident.Phase.DETECTION
        )

        if alerts:
            incident.alerts.set(alerts)

        # Log creation event
        incident.add_timeline_entry(
            'Incident created',
            created_by,
            f'Incident {incident.incident_number} created with {len(alerts) if alerts else 0} related alerts'
        )

        log_event(
            action='INCIDENT_CREATED',
            description=f'Incident {incident.incident_number} created: {title}',
            user=created_by,
            action_category=AuditLog.ActionCategory.ALERT,
            target_model='Incident',
            target_id=str(incident.id)
        )

        return incident

    @staticmethod
    def notify_stakeholders(alert, notification_type='created'):
        """
        Send email notifications to relevant stakeholders.

        Args:
            alert: Alert instance
            notification_type: 'created', 'acknowledged', 'resolved'
        """
        try:
            recipients = AlertService._get_notification_recipients(alert)

            if not recipients:
                logger.info(f"No recipients found for alert {alert.id}")
                return False

            subject_map = {
                'created': f'[{alert.severity}] New Security Alert: {alert.title}',
                'acknowledged': f'Alert Acknowledged: {alert.title}',
                'resolved': f'Alert Resolved: {alert.title}'
            }

            subject = subject_map.get(notification_type, 'Alert Notification')

            body_template = AlertService._get_notification_body(alert, notification_type)

            messages = [
                (subject, body_template, 'noreply@healthsec.local', [recipient.email])
                for recipient in recipients
            ]

            send_mass_mail(messages, fail_silently=False)
            logger.info(f"Notifications sent for alert {alert.id} to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.id}: {str(e)}")
            return False

    @staticmethod
    def _get_notification_recipients(alert):
        """Get list of users to notify based on alert severity and type."""
        recipients = []

        if alert.severity in [Alert.Severity.CRITICAL, Alert.Severity.HIGH]:
            recipients = list(User.objects.filter(
                role__in=['ADMIN', 'COMPLIANCE'],
                is_active=True
            ))
        elif alert.severity == Alert.Severity.MEDIUM:
            recipients = list(User.objects.filter(
                role__in=['ANALYST', 'COMPLIANCE', 'ADMIN'],
                is_active=True
            ))
        else:
            recipients = list(User.objects.filter(
                role__in=['ANALYST', 'ADMIN'],
                is_active=True
            ))

        if alert.assigned_to and alert.assigned_to.is_active:
            if alert.assigned_to not in recipients:
                recipients.append(alert.assigned_to)

        return recipients

    @staticmethod
    def _get_notification_body(alert, notification_type):
        """Generate notification email body."""
        base = f"""
Alert Details:
{'-' * 50}
Type: {alert.get_alert_type_display()}
Severity: {alert.severity}
Status: {alert.get_status_display()}
Title: {alert.title}

Description:
{alert.description}

System: {alert.affected_system.name if alert.affected_system else 'N/A'}
Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Please log in to HealthSec for more details.
"""
        return base

    @staticmethod
    def get_statistics(days=30):
        """
        Get alert and incident statistics for the past N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        cutoff = timezone.now() - timedelta(days=days)

        alerts = Alert.objects.filter(created_at__gte=cutoff)
        incidents = Incident.objects.filter(created_at__gte=cutoff)

        stats = {
            'total_alerts': alerts.count(),
            'total_incidents': incidents.count(),
            'alerts_by_severity': {
                'critical': alerts.filter(severity=Alert.Severity.CRITICAL).count(),
                'high': alerts.filter(severity=Alert.Severity.HIGH).count(),
                'medium': alerts.filter(severity=Alert.Severity.MEDIUM).count(),
                'low': alerts.filter(severity=Alert.Severity.LOW).count(),
            },
            'alerts_by_status': {
                'new': alerts.filter(status=Alert.Status.NEW).count(),
                'acknowledged': alerts.filter(status=Alert.Status.ACKNOWLEDGED).count(),
                'in_progress': alerts.filter(status=Alert.Status.IN_PROGRESS).count(),
                'resolved': alerts.filter(status=Alert.Status.RESOLVED).count(),
                'closed': alerts.filter(status=Alert.Status.CLOSED).count(),
                'false_positive': alerts.filter(status=Alert.Status.FALSE_POSITIVE).count(),
            },
            'alerts_by_type': {
                choice[0]: alerts.filter(alert_type=choice[0]).count()
                for choice in Alert.AlertType.choices
            },
            'incidents_by_phase': {
                choice[0]: incidents.filter(phase=choice[0]).count()
                for choice in Incident.Phase.choices
            },
            'open_alerts': alerts.exclude(
                status__in=[Alert.Status.RESOLVED, Alert.Status.CLOSED, Alert.Status.FALSE_POSITIVE]
            ).count(),
            'open_incidents': incidents.exclude(phase=Incident.Phase.CLOSED).count(),
            'avg_resolution_time': AlertService._calculate_avg_resolution_time(alerts),
        }

        return stats

    @staticmethod
    def _calculate_avg_resolution_time(alerts):
        """Calculate average time to resolution in hours."""
        resolved = alerts.filter(resolved_at__isnull=False)
        if not resolved.exists():
            return 0

        total_seconds = sum(
            (alert.resolved_at - alert.created_at).total_seconds()
            for alert in resolved
        )
        avg_seconds = total_seconds / resolved.count()
        return round(avg_seconds / 3600, 2)

    @staticmethod
    def evaluate_rules():
        """
        Evaluate all active alert rules and trigger matching rules.

        Returns:
            List of created Alert instances
        """
        created_alerts = []

        for rule in AlertRule.objects.filter(is_active=True):
            try:
                if AlertService._matches_rule_conditions(rule):
                    alert = AlertService.create_alert(
                        title=f"[{rule.name}] Rule triggered",
                        description=rule.description,
                        alert_type=rule.alert_type,
                        severity=rule.severity,
                    )
                    created_alerts.append(alert)

                    if rule.actions.get('notify'):
                        AlertService.notify_stakeholders(alert, 'created')

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {str(e)}")

        return created_alerts

    @staticmethod
    def _matches_rule_conditions(rule):
        """Check if alert rule conditions are met."""
        if rule.rule_type == AlertRule.RuleType.THRESHOLD:
            threshold_type = rule.conditions.get('type')
            threshold_value = rule.conditions.get('value', 0)

            if threshold_type == 'unresolved_alerts':
                count = Alert.objects.open().count()
                return count >= threshold_value
            elif threshold_type == 'critical_alerts':
                count = Alert.objects.filter(
                    severity=Alert.Severity.CRITICAL,
                    status=Alert.Status.NEW
                ).count()
                return count >= threshold_value

        return False

    @staticmethod
    def send_alert_email(alert, recipients=None):
        """
        Send alert email notification.

        Args:
            alert: Alert instance
            recipients: List of User instances or None (auto-fetch by role)

        Returns:
            bool: True if email sent successfully
        """
        return EmailNotificationService.send_alert_email(alert, recipients)

    @staticmethod
    def send_incident_email(incident):
        """
        Send incident notification email.

        Args:
            incident: Incident instance

        Returns:
            bool: True if email sent successfully
        """
        return EmailNotificationService.send_incident_notification(incident)

    @staticmethod
    def send_test_email(to_email):
        """
        Send a test email to verify email configuration.

        Args:
            to_email: Email address to send test to

        Returns:
            bool: True if email sent successfully
        """
        return EmailNotificationService.send_test_email(to_email)
