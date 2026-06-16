"""
Management command: send_test_email

Usage:
    python manage.py send_test_email your-email@example.com

Description:
    Sends a test email to verify SMTP configuration is working correctly.
    Useful for debugging email delivery issues.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from alerts.services import AlertService

User = get_user_model()


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP configuration.'

    def add_arguments(self, parser):
        parser.add_argument(
            'email_address',
            type=str,
            help='Email address to send test to',
        )

    def handle(self, *args, **options):
        email_address = options['email_address']

        self.stdout.write(
            self.style.WARNING(f'Sending test email to: {email_address}')
        )

        success = AlertService.send_test_email(email_address)

        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] Test email sent successfully to {email_address}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Check your inbox or email logs for the message.'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'[ERROR] Failed to send test email to {email_address}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Check your email configuration in settings.py and .env'
                )
            )
