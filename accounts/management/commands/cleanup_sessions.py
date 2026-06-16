"""
Management command: cleanup_sessions

Cleans up expired sessions from the database.
Removes sessions older than SESSION_COOKIE_AGE (default 30 days).

Scheduled to run weekly.

Usage: python manage.py cleanup_sessions [--verbose]
"""

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from audit.utils import log_event
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed information',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete sessions older than N days (default: 30)',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        days = options['days']

        self.stdout.write(self.style.WARNING(f'Cleaning up sessions older than {days} days...'))

        cutoff_date = timezone.now() - timedelta(days=days)

        expired_sessions = Session.objects.filter(expire_date__lt=cutoff_date)
        count = expired_sessions.count()

        if verbose:
            self.stdout.write(f"Found {count} expired sessions")

        expired_sessions.delete()

        # Log the action
        log_event(
            action='SESSION_CLEANUP',
            description=f'Cleaned up {count} expired sessions older than {days} days.',
        )

        self.stdout.write(
            self.style.SUCCESS(f'\n[OK] Session cleanup complete')
        )
        self.stdout.write(f"  Sessions deleted: {count}")

        return 0
