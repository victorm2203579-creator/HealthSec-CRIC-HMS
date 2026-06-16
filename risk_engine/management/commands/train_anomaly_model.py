"""
Management command: train_anomaly_model

Usage:
    python manage.py train_anomaly_model

Description:
    Trains the Isolation Forest anomaly detection model on historical
    access logs. Should be run periodically (weekly recommended) to
    update the model with new baseline behavior patterns.
"""

from django.core.management.base import BaseCommand
from risk_engine.ml_detector import AnomalyDetector


class Command(BaseCommand):
    help = 'Train the anomaly detection model on historical access logs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed training information',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('Starting anomaly detector training...')
        )

        detector = AnomalyDetector()
        result = detector.train()

        if result['success']:
            self.stdout.write(
                self.style.SUCCESS('[OK] Model trained successfully')
            )
            self.stdout.write(f"  Trained on {result['trained_records']} records")
            self.stdout.write(f"  Trained at {result['trained_at']}")

            if options['verbose']:
                self.stdout.write("\nModel Configuration:")
                self.stdout.write("  Algorithm: Isolation Forest")
                self.stdout.write("  Contamination rate: 0.1 (10%)")
                self.stdout.write("  Features: 11")
                self.stdout.write("  Feature names:")
                self.stdout.write("    - access_hour (0-23)")
                self.stdout.write("    - access_day_of_week (0-6)")
                self.stdout.write("    - is_weekend (0 or 1)")
                self.stdout.write("    - records_accessed_last_hour (count)")
                self.stdout.write("    - records_accessed_today (count)")
                self.stdout.write("    - is_after_hours (0 or 1)")
                self.stdout.write("    - is_cross_department (0 or 1)")
                self.stdout.write("    - sensitivity_level_encoded (0-3)")
                self.stdout.write("    - access_type_encoded (0-4)")
                self.stdout.write("    - user_avg_daily_accesses (count)")
                self.stdout.write("    - deviation_from_avg (stddev)")

        else:
            self.stdout.write(
                self.style.ERROR(f"[ERROR] Training failed: {result['message']}")
            )
            return 1

        self.stdout.write(
            self.style.SUCCESS('\nTraining complete. Model saved and ready for use.')
        )
        return 0
