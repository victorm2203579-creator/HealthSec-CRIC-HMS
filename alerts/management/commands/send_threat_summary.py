"""
Management command: send_threat_summary

Sends daily threat summary email to admins with:
- New threats detected in last 24 hours
- Open incidents count
- Critical alerts summary

Scheduled to run daily (morning time).

Usage: python manage.py send_threat_summary [--verbose]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import timedelta
from risk_engine.models import ThreatEvent
from alerts.models import Alert, Incident
from audit.utils import log_event
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send daily threat summary email to admins'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed information',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']

        self.stdout.write(self.style.WARNING('Generating threat summary...'))

        # Get data from last 24 hours
        since = timezone.now() - timedelta(hours=24)

        new_threats = ThreatEvent.objects.filter(
            detected_at__gte=since,
        ).order_by('-detected_at')

        open_incidents = Incident.objects.filter(
            phase__in=[Incident.Phase.INITIAL_RESPONSE, Incident.Phase.INVESTIGATION],
        )

        critical_alerts = Alert.objects.filter(
            created_at__gte=since,
            severity=Alert.Severity.CRITICAL,
        )

        # Get admin users
        admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)

        if not admins:
            self.stdout.write(self.style.WARNING("No active admins found"))
            return

        # Prepare email context
        context = {
            'threats_count': new_threats.count(),
            'threats': new_threats[:10],  # Top 10
            'incidents_count': open_incidents.count(),
            'critical_alerts_count': critical_alerts.count(),
            'summary_date': timezone.now().strftime('%Y-%m-%d'),
        }

        # Send to each admin
        for admin in admins:
            try:
                subject = f'[HealthSec] Daily Threat Summary - {context["summary_date"]}'

                # In production, use actual template
                message = f"""
Daily Threat Summary Report
==========================

Summary Date: {context['summary_date']}

New Threats (24h): {context['threats_count']}
Open Incidents: {context['incidents_count']}
Critical Alerts (24h): {context['critical_alerts_count']}

For detailed information, log in to the HealthSec dashboard.
                """

                send_mail(
                    subject,
                    message,
                    'noreply@healthsec.local',
                    [admin.email],
                    fail_silently=False,
                )

                if verbose:
                    self.stdout.write(f"Sent summary email to {admin.email}")

            except Exception as e:
                logger.error(f"Error sending email to {admin.email}: {e}")
                if verbose:
                    self.stdout.write(self.style.ERROR(f"Failed to send to {admin.email}"))

        # Log the action
        log_event(
            action='THREAT_SUMMARY_SENT',
            description=f'Threat summary sent to {admins.count()} admins. '
                       f'{new_threats.count()} new threats, '
                       f'{open_incidents.count()} open incidents, '
                       f'{critical_alerts.count()} critical alerts.',
        )

        self.stdout.write(
            self.style.SUCCESS(f'\n[OK] Threat summary complete')
        )
        self.stdout.write(f"  Recipients: {admins.count()}")
        self.stdout.write(f"  New threats: {new_threats.count()}")
        self.stdout.write(f"  Open incidents: {open_incidents.count()}")
        self.stdout.write(f"  Critical alerts: {critical_alerts.count()}")

        return 0
