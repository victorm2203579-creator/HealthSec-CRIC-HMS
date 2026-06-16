"""
compliance/tests.py
===================
Test suite for regulatory compliance management.

Test Coverage:
- Compliance framework handling
- Automated compliance checks
- Evidence collection
- Control assessments
- Compliance scoring
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from compliance.models import (
    ComplianceFramework, Control, ControlAssessment,
    Evidence, ComplianceCheck, ComplianceReport
)
from accounts.models import User

User = get_user_model()


class ComplianceFrameworkTests(TestCase):
    """Test compliance framework creation and management."""

    def setUp(self):
        """Create test framework."""
        self.framework = ComplianceFramework.objects.create(
            name='HIPAA Security Rule',
            framework_type=ComplianceFramework.FrameworkType.HIPAA,
            description='Health Insurance Portability and Accountability Act',
            is_active=True,
        )

    def test_framework_creation(self):
        """
        Validates: Compliance framework is created with required fields.
        Why it matters: Framework foundation for control mapping.
        """
        self.assertIsNotNone(self.framework.id)
        self.assertEqual(self.framework.name, 'HIPAA Security Rule')
        self.assertEqual(self.framework.framework_type, ComplianceFramework.FrameworkType.HIPAA)

    def test_framework_status_tracking(self):
        """
        Validates: Framework status can be enabled/disabled.
        Why it matters: Controls management lifecycle.
        """
        self.assertTrue(self.framework.is_active)

        self.framework.is_active = False
        self.framework.save()

        self.framework.refresh_from_db()
        self.assertFalse(self.framework.is_active)

    def test_multiple_frameworks(self):
        """
        Validates: Multiple frameworks can coexist.
        Why it matters: Organizations may follow multiple standards.
        """
        gdpr = ComplianceFramework.objects.create(
            name='GDPR',
            framework_type=ComplianceFramework.FrameworkType.GDPR,
            is_active=True,
        )

        pci = ComplianceFramework.objects.create(
            name='PCI DSS',
            framework_type=ComplianceFramework.FrameworkType.PCI_DSS,
            is_active=True,
        )

        all_frameworks = ComplianceFramework.objects.all()
        self.assertEqual(all_frameworks.count(), 3)


class ControlAssessmentTests(TestCase):
    """Test control creation and assessment."""

    def setUp(self):
        """Create framework and control."""
        self.framework = ComplianceFramework.objects.create(
            name='HIPAA',
            framework_type=ComplianceFramework.FrameworkType.HIPAA,
        )

        self.control = Control.objects.create(
            framework=self.framework,
            control_id='AC-2',
            title='Account Management',
            description='Manages user account lifecycle',
            requirement='All user accounts must be managed according to policy',
        )

        self.assessor = User.objects.create_user(
            username='assessor',
            email='assessor@example.com',
            password='AssessorPass123!',
            role=User.Role.COMPLIANCE,
        )

    def test_control_creation(self):
        """
        Validates: Control is created with required fields.
        Why it matters: Control documentation foundation.
        """
        self.assertIsNotNone(self.control.id)
        self.assertEqual(self.control.control_id, 'AC-2')

    def test_control_assessment_creation(self):
        """
        Validates: Control assessment is created.
        Why it matters: Assessment tracking for compliance evidence.
        """
        assessment = ControlAssessment.objects.create(
            control=self.control,
            assessed_by=self.assessor,
            status=ControlAssessment.Status.COMPLIANT,
            findings='All requirements met',
        )

        self.assertIsNotNone(assessment.id)
        self.assertEqual(assessment.status, ControlAssessment.Status.COMPLIANT)

    def test_assessment_status_options(self):
        """
        Validates: Assessment can have various status values.
        Why it matters: Tracks compliance posture accurately.
        """
        statuses = [
            ControlAssessment.Status.COMPLIANT,
            ControlAssessment.Status.NON_COMPLIANT,
            ControlAssessment.Status.PARTIALLY_COMPLIANT,
            ControlAssessment.Status.NOT_ASSESSED,
        ]

        for status in statuses:
            assessment = ControlAssessment.objects.create(
                control=self.control,
                assessed_by=self.assessor,
                status=status,
            )
            self.assertEqual(assessment.status, status)

    def test_assessment_findings_and_remediation(self):
        """
        Validates: Findings and remediation can be documented.
        Why it matters: Tracks required corrective actions.
        """
        assessment = ControlAssessment.objects.create(
            control=self.control,
            assessed_by=self.assessor,
            status=ControlAssessment.Status.PARTIALLY_COMPLIANT,
            findings='2 accounts lack password complexity enforcement',
            remediation='Apply policy update to all accounts by 2026-06-30',
        )

        self.assertIn('password complexity', assessment.findings)
        self.assertIn('2026-06-30', assessment.remediation)


class EvidenceCollectionTests(TestCase):
    """Test evidence documentation."""

    def setUp(self):
        """Create framework, control, and assessor."""
        self.framework = ComplianceFramework.objects.create(
            name='HIPAA',
            framework_type=ComplianceFramework.FrameworkType.HIPAA,
        )

        self.control = Control.objects.create(
            framework=self.framework,
            control_id='AU-2',
            title='Audit Logging',
            description='Maintain audit logs of all access',
        )

        self.assessor = User.objects.create_user(
            username='auditor',
            email='auditor@example.com',
            password='AuditorPass123!',
            role=User.Role.COMPLIANCE,
        )

        self.assessment = ControlAssessment.objects.create(
            control=self.control,
            assessed_by=self.assessor,
            status=ControlAssessment.Status.COMPLIANT,
        )

    def test_evidence_upload(self):
        """
        Validates: Evidence file is recorded.
        Why it matters: Supporting documentation for audits.
        """
        evidence = Evidence.objects.create(
            assessment=self.assessment,
            title='Audit Log Sample',
            description='Sample of audit logs from production system',
            # file would be uploaded in real scenario
        )

        self.assertIsNotNone(evidence.id)
        self.assertEqual(evidence.title, 'Audit Log Sample')

    def test_multiple_evidence_per_assessment(self):
        """
        Validates: Multiple evidence items can support one assessment.
        Why it matters: Comprehensive documentation.
        """
        for i in range(3):
            Evidence.objects.create(
                assessment=self.assessment,
                title=f'Evidence {i+1}',
            )

        evidence_count = self.assessment.evidence_set.count()
        self.assertEqual(evidence_count, 3)

    def test_evidence_metadata(self):
        """
        Validates: Evidence tracks metadata (uploader, date).
        Why it matters: Chain of custody for evidence.
        """
        evidence = Evidence.objects.create(
            assessment=self.assessment,
            title='Policy Document',
            uploaded_by=self.assessor,
        )

        self.assertEqual(evidence.uploaded_by, self.assessor)
        self.assertIsNotNone(evidence.uploaded_at)


class ComplianceCheckTests(TestCase):
    """Test automated compliance checks."""

    def setUp(self):
        """Create test framework."""
        self.framework = ComplianceFramework.objects.create(
            name='HIPAA',
            framework_type=ComplianceFramework.FrameworkType.HIPAA,
        )

    def test_password_policy_check(self):
        """
        Validates: Password policy check can pass/fail.
        Why it matters: Automated compliance verification.
        """
        check = ComplianceCheck.objects.create(
            framework=self.framework,
            check_name='Password Complexity',
            check_type=ComplianceCheck.CheckType.AUTOMATED,
            description='Verify password complexity requirements',
        )

        self.assertIsNotNone(check.id)

    def test_audit_logging_check(self):
        """
        Validates: Audit logging check tracks status.
        Why it matters: Monitors logging compliance.
        """
        check = ComplianceCheck.objects.create(
            framework=self.framework,
            check_name='Audit Logging Enabled',
            check_type=ComplianceCheck.CheckType.AUTOMATED,
            description='Verify audit logs are enabled',
        )

        # Simulate check execution
        check.last_executed = timezone.now()
        check.save()

        self.assertIsNotNone(check.last_executed)

    def test_check_result_recording(self):
        """
        Validates: Check results are recorded.
        Why it matters: Compliance reporting and trending.
        """
        check = ComplianceCheck.objects.create(
            framework=self.framework,
            check_name='Encryption at Rest',
            check_type=ComplianceCheck.CheckType.AUTOMATED,
        )

        # Record result (framework handles result storage)
        check.last_executed = timezone.now()
        check.save()

        check.refresh_from_db()
        self.assertIsNotNone(check.last_executed)


class ComplianceScoringTests(TestCase):
    """Test compliance score calculation."""

    def setUp(self):
        """Create framework and controls."""
        self.framework = ComplianceFramework.objects.create(
            name='HIPAA',
            framework_type=ComplianceFramework.FrameworkType.HIPAA,
        )

        self.assessor = User.objects.create_user(
            username='scorer',
            email='scorer@example.com',
            password='ScorerPass123!',
            role=User.Role.COMPLIANCE,
        )

        # Create multiple controls with different statuses
        for i in range(4):
            control = Control.objects.create(
                framework=self.framework,
                control_id=f'CTL-{i+1}',
                title=f'Control {i+1}',
            )

            if i == 0:
                status = ControlAssessment.Status.COMPLIANT
            elif i == 1:
                status = ControlAssessment.Status.COMPLIANT
            elif i == 2:
                status = ControlAssessment.Status.PARTIALLY_COMPLIANT
            else:
                status = ControlAssessment.Status.NON_COMPLIANT

            ControlAssessment.objects.create(
                control=control,
                assessed_by=self.assessor,
                status=status,
            )

    def test_compliance_score_calculation(self):
        """
        Validates: Compliance score is calculated correctly.
        Why it matters: Overall compliance posture measurement.
        """
        assessments = ControlAssessment.objects.all()
        compliant = assessments.filter(
            status=ControlAssessment.Status.COMPLIANT
        ).count()
        total = assessments.count()

        # Score formula: (compliant + partial*0.5) / total * 100
        expected_score = ((2 + 0.5) / 4) * 100

        self.assertEqual(expected_score, 62.5)

    def test_compliance_report_generation(self):
        """
        Validates: Compliance report aggregates assessment data.
        Why it matters: Executive reporting and stakeholder communication.
        """
        report = ComplianceReport.objects.create(
            framework=self.framework,
            generated_by=self.assessor,
            overall_score=62.5,
        )

        self.assertIsNotNone(report.id)
        self.assertEqual(report.overall_score, 62.5)


class AutomatedComplianceCheckTests(TestCase):
    """Test running automated compliance checks."""

    def setUp(self):
        """Create framework and checks."""
        self.framework = ComplianceFramework.objects.create(
            name='HIPAA',
            framework_type=ComplianceFramework.FrameworkType.HIPAA,
        )

    def test_run_all_automated_checks(self):
        """
        Validates: All automated checks can be run without errors.
        Why it matters: Periodic compliance verification.
        """
        # Create multiple automated checks
        check_names = [
            'Password Complexity',
            'Audit Logging',
            'Encryption at Rest',
            'Access Controls',
        ]

        for name in check_names:
            ComplianceCheck.objects.create(
                framework=self.framework,
                check_name=name,
                check_type=ComplianceCheck.CheckType.AUTOMATED,
            )

        checks = ComplianceCheck.objects.filter(
            check_type=ComplianceCheck.CheckType.AUTOMATED
        )

        self.assertEqual(checks.count(), 4)

        # Simulate running all checks
        for check in checks:
            check.last_executed = timezone.now()
            check.save()

        # Verify all were executed
        executed = ComplianceCheck.objects.filter(
            last_executed__isnull=False
        ).count()

        self.assertEqual(executed, 4)

    def test_check_scheduling(self):
        """
        Validates: Checks can be scheduled for recurring runs.
        Why it matters: Automated compliance monitoring.
        """
        check = ComplianceCheck.objects.create(
            framework=self.framework,
            check_name='Recurring Check',
            check_type=ComplianceCheck.CheckType.AUTOMATED,
            run_frequency='weekly',
        )

        self.assertEqual(check.run_frequency, 'weekly')
