"""
Management command: run_anomaly_scan

Usage:
    python manage.py run_anomaly_scan [--days 7] [--verbose]

Description:
    Runs anomaly detection on recent access logs (past N days).
    Creates SuspiciousActivity records for flagged accesses.
    Model must be trained first.
"""

from django.core.management.base import BaseCommand, CommandError
from risk_engine.ml_detector import AnomalyDetector


class Command(BaseCommand):
    help = 'Run anomaly detection scan on recent access logs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed scan information',
        )

    def handle(self, *args, **options):
        days = options['days']

        detector = AnomalyDetector()

        # Check if model is trained
        status = detector.get_model_status()
        if not status['is_trained']:
            raise CommandError(
                'Model is not trained. Run "python manage.py train_anomaly_model" first.'
            )

        self.stdout.write(
            self.style.WARNING(f'Running anomaly scan on last {days} days...')
        )

        if options['verbose']:
            self.stdout.write(
                f"Model trained at: {status['trained_at']}"
            )
            self.stdout.write(
                f"Trained on {status['trained_records']} records"
            )

        result = detector.batch_analyze(days=days)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[RESULTS]'))
        self.stdout.write(f"  Analyzed: {result['analyzed']} access logs")
        self.stdout.write(f"  Anomalies: {result['anomalies_found']} detected")

        if result['anomalies_found'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[ALERT] {result['anomalies_found']} suspicious activities created"
                )
            )
            self.stdout.write(
                "Review them in the admin panel or use the monitoring dashboard."
            )

        if options['verbose']:
            anomaly_rate = (
                (result['anomalies_found'] / result['analyzed'] * 100)
                if result['analyzed'] > 0
                else 0
            )
            self.stdout.write(f"\nAnomaly rate: {anomaly_rate:.2f}%")

        self.stdout.write(
            self.style.SUCCESS('\nScan complete.')
        )
        return 0
