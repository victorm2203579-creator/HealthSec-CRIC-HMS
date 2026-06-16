"""
monitoring/tests.py
===================
Test suite for healthcare information monitoring and anomaly detection.

Test Coverage:
- Patient record access logging
- Suspicious activity flagging
- Suspicion score calculation
- Monitoring engine analysis
- After-hours access detection
- Bulk access detection
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from monitoring.models import (
    PatientRecord, RecordAccessLog, SuspiciousActivity,
    HealthcareSystem, MonitoringEvent, DataAsset
)
from monitoring.engine import MonitoringEngine

User = get_user_model()


class RecordAccessLoggingTests(TestCase):
    """Test access logging and record creation."""

    def setUp(self):
        """Create test user and patient record."""
        self.user = User.objects.create_user(
            username='clinician',
            email='clinician@example.com',
            password='ClinicianPass123!',
            department='Cardiology',
            role=User.Role.ANALYST,
        )

        self.patient_record = PatientRecord.objects.create(
            patient_code='PAT-00001',
            record_type=PatientRecord.RecordType.MEDICAL_HISTORY,
            sensitivity_level=PatientRecord.SensitivityLevel.CRITICAL,
            department='Cardiology',
            created_by=self.user,
        )

    def test_record_access_creates_log(self):
        """
        Validates: Accessing a record creates a RecordAccessLog entry.
        Why it matters: All access must be logged for audit trail.
        """
        access_log = RecordAccessLog.objects.create(
            user=self.user,
            patient_record=self.patient_record,
            access_type=RecordAccessLog.AccessType.VIEW,
            access_hour=14,
            device_info='Chrome/Windows',
        )

        self.assertIsNotNone(access_log.log_id)
        self.assertEqual(access_log.access_type, RecordAccessLog.AccessType.VIEW)
        self.assertEqual(RecordAccessLog.objects.count(), 1)

    def test_access_log_stores_all_fields(self):
        """
        Validates: Access log captures all required fields.
        Why it matters: Complete information needed for forensics.
        """
        access_log = RecordAccessLog.objects.create(
            user=self.user,
            patient_record=self.patient_record,
            access_type=RecordAccessLog.AccessType.DOWNLOAD,
            access_hour=9,
            device_info='Firefox/MacOS',
        )

        self.assertEqual(access_log.user, self.user)
        self.assertEqual(access_log.patient_record, self.patient_record)
        self.assertEqual(access_log.access_type, RecordAccessLog.AccessType.DOWNLOAD)
        self.assertIsNotNone(access_log.timestamp)

    def test_multiple_access_logs_tracked(self):
        """
        Validates: Multiple accesses by same user are all logged.
        Why it matters: Pattern analysis requires complete log history.
        """
        for i in range(5):
            RecordAccessLog.objects.create(
                user=self.user,
                patient_record=self.patient_record,
                access_type=RecordAccessLog.AccessType.VIEW,
                access_hour=i,
                device_info='Device-' + str(i),
            )

        user_logs = RecordAccessLog.objects.filter(user=self.user)
        self.assertEqual(user_logs.count(), 5)


class SuspiciousActivityDetectionTests(TestCase):
    """Test detection and flagging of suspicious access patterns."""

    def setUp(self):
        """Create test infrastructure."""
        self.user = User.objects.create_user(
            username='suspect',
            email='suspect@example.com',
            password='SuspectPass123!',
            department='Finance',
            role=User.Role.ANALYST,
        )

        self.record = PatientRecord.objects.create(
            patient_code='PAT-00002',
            record_type=PatientRecord.RecordType.INSURANCE,
            sensitivity_level=PatientRecord.SensitivityLevel.CRITICAL,
            department='Clinical',  # Different from user's department
            created_by=self.user,
        )

        self.engine = MonitoringEngine()

    def test_after_hours_flagged(self):
        """
        Validates: Access at 2AM is flagged as after-hours.
        Why it matters: After-hours access to PHI is suspicious.
        """
        # Create access log at 2 AM (hour=2)
        access_log = RecordAccessLog.objects.create(
            user=self.user,
            patient_record=self.record,
            access_type=RecordAccessLog.AccessType.VIEW,
            access_hour=2,
            device_info='WorkstationA',
        )

        # Analyze the access
        score, flags = self.engine.analyze_access(access_log)

        self.assertIn('after_hours', flags)
        self.assertGreater(score, 0)

    def test_bulk_access_flagged(self):
        """
        Validates: Accessing 15 records in 1 hour is flagged.
        Why it matters: Bulk access may indicate data exfiltration.
        """
        # Create multiple access logs within 1 hour
        for i in range(15):
            record = PatientRecord.objects.create(
                patient_code=f'PAT-BULK-{i:03d}',
                record_type=PatientRecord.RecordType.LAB_RESULT,
                sensitivity_level=PatientRecord.SensitivityLevel.MEDIUM,
                department='Lab',
                created_by=self.user,
            )
            RecordAccessLog.objects.create(
                user=self.user,
                patient_record=record,
                access_type=RecordAccessLog.AccessType.VIEW,
                access_hour=9,
                device_info='Workstation',
            )

        # Last access is the one being analyzed
        last_log = RecordAccessLog.objects.last()
        score, flags = self.engine.analyze_access(last_log)

        self.assertIn('bulk_access', flags)

    def test_cross_department_access_flagged(self):
        """
        Validates: Cross-department access is flagged.
        Why it matters: Accessing outside own department is suspicious.
        """
        # User in Finance accessing Clinical record
        access_log = RecordAccessLog.objects.create(
            user=self.user,  # department='Finance'
            patient_record=self.record,  # department='Clinical'
            access_type=RecordAccessLog.AccessType.VIEW,
            access_hour=14,
            device_info='Workstation',
        )

        score, flags = self.engine.analyze_access(access_log)

        self.assertIn('cross_department', flags)

    def test_critical_record_access_flagged(self):
        """
        Validates: Access to CRITICAL sensitivity record is flagged.
        Why it matters: Highest sensitivity data needs extra scrutiny.
        """
        access_log = RecordAccessLog.objects.create(
            user=self.user,
            patient_record=self.record,  # CRITICAL sensitivity
            access_type=RecordAccessLog.AccessType.VIEW,
            access_hour=9,
            device_info='Workstation',
        )

        score, flags = self.engine.analyze_access(access_log)

        self.assertIn('critical_record', flags)

    def test_unknown_device_flagged(self):
        """
        Validates: Access from previously unseen device is flagged.
        Why it matters: Unknown devices may indicate compromise.
        """
        # First access from Device-A (should not be flagged as unknown)
        log1 = RecordAccessLog.objects.create(
            user=self.user,
            patient_record=self.record,
            access_type=RecordAccessLog.AccessType.VIEW,
            access_hour=9,
            device_info='Device-A',
        )

        # Second access from Device-B (new, should be flagged)
        log2 = RecordAccessLog.objects.create(
            user=self.user,
            patient_record=self.record,
            access_type=RecordAccessLog.AccessType.VIEW,
            access_hour=10,
            device_info='Device-B',
        )

        score, flags = self.engine.analyze_access(log2)

        self.assertIn('unknown_device', flags)


class SuspicionScoreCalculationTests(TestCase):
    """Test suspicion score formula and weighting."""

    def setUp(self):
        """Create monitoring engine."""
        self.engine = MonitoringEngine()

    def test_score_calculation_single_flag(self):
        """
        Validates: Single flag produces correct weighted score.
        Why it matters: Score weighting determines alert priority.
        """
        # after_hours has weight 25
        flags = ['after_hours']
        score = self.engine.calculate_suspicion_score(flags)

        self.assertEqual(score, 25)

    def test_score_calculation_multiple_flags(self):
        """
        Validates: Multiple flags sum correctly.
        Why it matters: Accurate composite risk assessment.
        """
        # after_hours (25) + bulk_access (30) + cross_department (20)
        flags = ['after_hours', 'bulk_access', 'cross_department']
        score = self.engine.calculate_suspicion_score(flags)

        self.assertEqual(score, 75)

    def test_score_capped_at_100(self):
        """
        Validates: Score cannot exceed 100.
        Why it matters: Prevents overflow in scoring system.
        """
        # All flags sum to more than 100
        flags = [
            'after_hours', 'bulk_access', 'cross_department',
            'critical_record', 'unknown_device', 'ml_anomaly'
        ]
        score = self.engine.calculate_suspicion_score(flags)

        self.assertEqual(score, 100)

    def test_score_zero_for_no_flags(self):
        """
        Validates: No flags results in score of 0.
        Why it matters: Clean/legitimate access has low risk.
        """
        flags = []
        score = self.engine.calculate_suspicion_score(flags)

        self.assertEqual(score, 0)

    def test_ml_anomaly_weight(self):
        """
        Validates: ML anomaly flag has correct weight (35).
        Why it matters: ML detection is significant indicator.
        """
        flags = ['ml_anomaly']
        score = self.engine.calculate_suspicion_score(flags)

        self.assertEqual(score, 35)


class MonitoringEngineAnalysisTests(TestCase):
    """Test full monitoring engine analysis flow."""

    def setUp(self):
        """Create test user and patient record."""
        self.user = User.objects.create_user(
            username='analyst',
            email='analyst@example.com',
            password='AnalystPass123!',
            department='Clinical',
            role=User.Role.ANALYST,
        )

        self.record = PatientRecord.objects.create(
            patient_code='PAT-00003',
            record_type=PatientRecord.RecordType.PRESCRIPTION,
            sensitivity_level=PatientRecord.SensitivityLevel.HIGH,
            department='Clinical',
            created_by=self.user,
        )

        self.engine = MonitoringEngine()

    def test_analyze_access_returns_tuple(self):
        """
        Validates: analyze_access returns (score, flags) tuple.
        Why it matters: Correct output format for downstream processing.
        """
        access_log = RecordAccessLog.objects.create(
            user=self.user,
            patient_record=self.record,
            access_type=RecordAccessLog.AccessType.VIEW,
            access_hour=14,
            device_info='Workstation',
        )

        result = self.engine.analyze_access(access_log)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        score, flags = result
        self.assertIsInstance(score, int)
        self.assertIsInstance(flags, list)

    def test_normal_access_low_score(self):
        """
        Validates: Normal access during business hours scores low.
        Why it matters: Reduces false positives for legitimate usage.
        """
        access_log = RecordAccessLog.objects.create(
            user=self.user,
            patient_record=self.record,
            access_type=RecordAccessLog.AccessType.VIEW,
            access_hour=9,  # Business hours
            device_info='Workstation',
        )

        score, flags = self.engine.analyze_access(access_log)

        # Normal access should have lower score than suspicious access
        # (exact score depends on sensitivity level and other factors)
        self.assertLess(score, 80)

    def test_suspicious_access_high_score(self):
        """
        Validates: Clearly suspicious access scores above threshold.
        Why it matters: Alerts are triggered for high-risk activity.
        """
        # Create bulk access (15 records in 1 hour)
        for i in range(15):
            record = PatientRecord.objects.create(
                patient_code=f'PAT-{i:04d}',
                record_type=PatientRecord.RecordType.LAB_RESULT,
                sensitivity_level=PatientRecord.SensitivityLevel.CRITICAL,
                department='Lab',
            )
            RecordAccessLog.objects.create(
                user=self.user,
                patient_record=record,
                access_type=RecordAccessLog.AccessType.DOWNLOAD,
                access_hour=2,  # After-hours
                device_info='NewDevice',
            )

        last_log = RecordAccessLog.objects.last()
        score, flags = self.engine.analyze_access(last_log)

        self.assertGreater(score, 40)  # Above SUSPICION_THRESHOLD
        self.assertGreater(len(flags), 1)


class HealthcareSystemMonitoringTests(TestCase):
    """Test monitoring of healthcare systems and data assets."""

    def setUp(self):
        """Create test healthcare system."""
        self.system = HealthcareSystem.objects.create(
            name='Test EHR',
            system_type=HealthcareSystem.SystemType.EHR,
            vendor='Epic Systems',
            ip_address='192.168.1.10',
            contains_phi=True,
        )

    def test_system_creation(self):
        """
        Validates: Healthcare system is created with required fields.
        Why it matters: Systems must be properly registered for monitoring.
        """
        self.assertIsNotNone(self.system.id)
        self.assertEqual(self.system.name, 'Test EHR')
        self.assertTrue(self.system.contains_phi)

    def test_system_status_tracking(self):
        """
        Validates: System status is tracked and updated.
        Why it matters: Availability monitoring for critical systems.
        """
        self.system.status = HealthcareSystem.Status.DEGRADED
        self.system.save()

        self.system.refresh_from_db()
        self.assertEqual(self.system.status, HealthcareSystem.Status.DEGRADED)

    def test_data_asset_classification(self):
        """
        Validates: Data assets are properly classified.
        Why it matters: PHI vs non-PHI affects risk scoring.
        """
        asset = DataAsset.objects.create(
            system=self.system,
            name='Patient Database',
            classification=DataAsset.DataClassification.PHI,
            record_count=100000,
            encrypted_at_rest=True,
        )

        self.assertEqual(asset.classification, DataAsset.DataClassification.PHI)
        self.assertTrue(asset.encrypted_at_rest)
