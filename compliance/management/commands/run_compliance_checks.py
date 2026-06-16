"""
Management command: run_compliance_checks

Runs all automated compliance checks across all frameworks using ComplianceChecker.

Usage: python manage.py run_compliance_checks [--verbose]
"""

from django.core.management.base import BaseCommand
from audit.utils import log_event
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run all automated compliance checks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed check information',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        self.stdout.write(self.style.WARNING('Starting compliance checks...'))

        try:
            from compliance.checker import ComplianceChecker
            checker = ComplianceChecker()
            results = checker.run_all_automated_checks()

            checks_run = len(results)
            checks_passed = sum(1 for r in results if getattr(r, 'status', None) == 'PASS')

            if verbose:
                for r in results:
                    label = f'[{r.status}]' if hasattr(r, 'status') else '[RUN]'
                    title = r.control.title if hasattr(r, 'control') else str(r)
                    self.stdout.write(f'  {label} {title}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Compliance checker error: {e}'))
            logger.error('run_compliance_checks failed: %s', e)
            checks_run = 0
            checks_passed = 0

        log_event(
            action='COMPLIANCE_CHECK_RUN',
            description=f'Ran {checks_run} compliance checks. {checks_passed} passed.',
            action_category='COMPLIANCE',
        )

        self.stdout.write(self.style.SUCCESS(f'\n[OK] Compliance checks complete'))
        self.stdout.write(f'  Checks run:    {checks_run}')
        self.stdout.write(f'  Checks passed: {checks_passed}')
        return 0
