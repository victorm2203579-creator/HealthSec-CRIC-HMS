"""
alerts/email_service.py
=======================
Email notification service for alerts, incidents, and compliance notifications.

HIPAA Compliance Notes:
- No patient PHI (names, MRNs, addresses) in emails
- Uses opaque internal IDs for cross-referencing
- All email sends logged to AuditLog
- Subject lines do not expose sensitive details
"""

import logging
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse

from audit.utils import log_event

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending security and compliance email notifications."""

    @staticmethod
    def send_alert_email(alert_instance, recipients=None):
        """
        Send alert notification email to security team.

        Args:
            alert_instance: Alert model instance
            recipients: List of User instances or None (auto-fetch by role)

        Returns:
            bool: True if sent successfully, False otherwise

        HIPAA: Only includes alert ID, type, severity. No system PHI exposed.
        """
        try:
            if recipients is None:
                recipients = EmailNotificationService._get_alert_recipients(alert_instance)

            if not recipients:
                logger.info(f"No recipients found for alert {alert_instance.id}")
                return False

            recipient_emails = [user.email for user in recipients if user.email]

            if not recipient_emails:
                logger.warning(f"No valid email addresses for alert {alert_instance.id}")
                return False

            context = {
                'alert': alert_instance,
                'alert_url': EmailNotificationService._build_absolute_url(
                    'alerts:alert_detail', kwargs={'pk': alert_instance.pk}
                ),
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'HealthSec CRIC HMS',
            }

            subject = f"[{alert_instance.severity}] Security Alert #{str(alert_instance.id)[:8]}"
            html_message = render_to_string('emails/alert_email.html', context)
            plain_message = render_to_string('emails/alert_email.txt', context)

            email = EmailMessage(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_emails,
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)

            log_event(
                action='ALERT_EMAIL_SENT',
                description=f'Alert {alert_instance.id} emailed to {len(recipient_emails)} recipients'
            )

            logger.info(f"Alert email sent for {alert_instance.id} to {len(recipient_emails)} recipients")
            return True

        except Exception as e:
            logger.error(f"Error sending alert email for {alert_instance.id}: {str(e)}")
            log_event(
                action='ALERT_EMAIL_FAILED',
                description=f'Failed to send alert email: {str(e)}'
            )
            return False

    @staticmethod
    def send_account_locked_email(user_instance, lock_reason="Security violation", unlock_time=None):
        """
        Send account lock notification to user and admins.

        Args:
            user_instance: User model instance
            lock_reason: Reason for account lock
            unlock_time: Expected unlock time (timezone-aware datetime)

        Returns:
            bool: True if sent successfully
        """
        try:
            recipient_emails = [user_instance.email]
            admin_users = User.objects.filter(role='ADMIN', is_active=True)
            recipient_emails.extend([admin.email for admin in admin_users if admin.email])

            context = {
                'user': user_instance,
                'lock_reason': lock_reason,
                'lock_time': timezone.now(),
                'unlock_time': unlock_time,
                'admin_url': EmailNotificationService._build_absolute_url('admin:index'),
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'HealthSec CRIC HMS',
            }

            subject = f"Account Lock Notification: {user_instance.username}"
            html_message = render_to_string('emails/account_locked_email.html', context)
            plain_message = render_to_string('emails/account_locked_email.txt', context)

            email = EmailMessage(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_emails,
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)

            log_event(
                action='ACCOUNT_LOCKED_EMAIL_SENT',
                description=f'Account lock notification sent for {user_instance.username}'
            )

            logger.info(f"Account lock email sent for {user_instance.username}")
            return True

        except Exception as e:
            logger.error(f"Error sending account lock email for {user_instance.username}: {str(e)}")
            return False

    @staticmethod
    def send_compliance_notification(report_instance):
        """
        Send compliance check notification to compliance and admin roles.

        Args:
            report_instance: GeneratedReport model instance

        Returns:
            bool: True if sent successfully
        """
        try:
            recipients = User.objects.filter(
                role__in=['COMPLIANCE', 'ADMIN'],
                is_active=True
            ).distinct()

            recipient_emails = [user.email for user in recipients if user.email]

            if not recipient_emails:
                logger.warning("No recipients for compliance notification")
                return False

            context = {
                'report': report_instance,
                'report_url': EmailNotificationService._build_absolute_url(
                    'reports:report_detail', kwargs={'pk': report_instance.pk}
                ),
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'HealthSec CRIC HMS',
            }

            subject = f"Compliance Report Generated: {report_instance.report_type}"
            html_message = render_to_string('emails/compliance_report_email.html', context)
            plain_message = render_to_string('emails/compliance_report_email.txt', context)

            email = EmailMessage(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_emails,
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)

            log_event(
                action='COMPLIANCE_REPORT_EMAIL_SENT',
                description=f'Compliance report {report_instance.id} emailed to {len(recipient_emails)} recipients'
            )

            logger.info(f"Compliance email sent to {len(recipient_emails)} recipients")
            return True

        except Exception as e:
            logger.error(f"Error sending compliance notification: {str(e)}")
            return False

    @staticmethod
    def send_incident_notification(incident_instance):
        """
        Send new incident notification to security and admin roles.

        Args:
            incident_instance: Incident model instance

        Returns:
            bool: True if sent successfully
        """
        try:
            recipients = User.objects.filter(
                role__in=['ADMIN', 'ANALYST'],
                is_active=True
            ).distinct()

            recipient_emails = [user.email for user in recipients if user.email]

            if not recipient_emails:
                logger.warning("No recipients for incident notification")
                return False

            context = {
                'incident': incident_instance,
                'incident_url': EmailNotificationService._build_absolute_url(
                    'alerts:incident_detail', kwargs={'pk': incident_instance.pk}
                ),
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'HealthSec CRIC HMS',
            }

            subject = f"[INCIDENT] {incident_instance.incident_number}: {incident_instance.title}"
            html_message = render_to_string('emails/incident_notification_email.html', context)
            plain_message = render_to_string('emails/incident_notification_email.txt', context)

            email = EmailMessage(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_emails,
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)

            log_event(
                action='INCIDENT_EMAIL_SENT',
                description=f'Incident {incident_instance.incident_number} emailed to {len(recipient_emails)} recipients'
            )

            logger.info(f"Incident email sent for {incident_instance.incident_number}")
            return True

        except Exception as e:
            logger.error(f"Error sending incident notification: {str(e)}")
            return False

    @staticmethod
    def send_test_email(to_email):
        """
        Send a test email to verify email configuration.

        Args:
            to_email: Email address to send test to

        Returns:
            bool: True if sent successfully
        """
        try:
            subject = "HealthSec Email Configuration Test"
            message = "This is a test email from HealthSec CRIC HMS. If you receive this, your email configuration is working correctly."
            from_email = settings.DEFAULT_FROM_EMAIL

            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False,
            )

            log_event(
                action='TEST_EMAIL_SENT',
                description=f'Test email sent to {to_email}'
            )

            logger.info(f"Test email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending test email to {to_email}: {str(e)}")
            log_event(
                action='TEST_EMAIL_FAILED',
                description=f'Test email failed: {str(e)}'
            )
            return False

    @staticmethod
    def _get_alert_recipients(alert_instance):
        """
        Get list of users to notify based on alert severity and role.

        HIPAA: Only returns active users with email addresses.
        Implements minimum necessary access principle.
        """
        recipients = []

        if alert_instance.severity in [alert_instance.Severity.CRITICAL, alert_instance.Severity.HIGH]:
            recipients = list(User.objects.filter(
                role__in=['ADMIN', 'COMPLIANCE'],
                is_active=True
            ))
        elif alert_instance.severity == alert_instance.Severity.MEDIUM:
            recipients = list(User.objects.filter(
                role__in=['ANALYST', 'COMPLIANCE', 'ADMIN'],
                is_active=True
            ))
        else:
            recipients = list(User.objects.filter(
                role__in=['ANALYST', 'ADMIN'],
                is_active=True
            ))

        if alert_instance.assigned_to and alert_instance.assigned_to.is_active:
            if alert_instance.assigned_to not in recipients:
                recipients.append(alert_instance.assigned_to)

        return recipients

    @staticmethod
    def _build_absolute_url(view_name, kwargs=None):
        """
        Build absolute URL for email links.

        Returns:
            str: Full absolute URL including scheme and domain
        """
        try:
            from django.urls import reverse

            relative_url = reverse(view_name, kwargs=kwargs or {})
            scheme = 'https' if not settings.DEBUG else 'http'
            domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
            return f"{scheme}://{domain}{relative_url}"
        except Exception as e:
            logger.error(f"Error building absolute URL: {str(e)}")
            return "#"
