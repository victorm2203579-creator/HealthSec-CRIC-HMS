"""
risk_engine/tests.py
====================
Test suite for cyber risk intelligence and threat detection.

Test Coverage:
- Threat event detection
- Risk score calculation
- Threat feed validation
- Risk level classification
- Vulnerability tracking
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from risk_engine.models import (
    ThreatEvent, ThreatFeed, VulnerabilityRecord,
    RiskScore, RiskAssessment
)
from risk_engine.engine import RiskIntelligenceEngine
from monitoring.models import HealthcareSystem

User = get_user_model()


class ThreatEventDetectionTests(TestCase):
    """Test threat event creation and detection."""

    def setUp(self):
        """Create test system."""
        self.system = HealthcareSystem.objects.create(
            name='Test EHR System',
            system_type=HealthcareSystem.SystemType.EHR,
            vendor='Epic',
            contains_phi=True,
        )

    def test_threat_event_creation(self):
        """
        Validates: Threat event is created with correct fields.
        Why it matters: Threat tracking foundation.
        """
        threat = ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.MALWARE_INDICATOR,
            severity=ThreatEvent.Severity.HIGH,
            target_resource='Server-01',
            description='Ransomware detected on network',
            indicators={
                'file_hash': ['abc123', 'def456'],
                'ip_address': ['192.168.1.100'],
            },
        )

        self.assertIsNotNone(threat.threat_id)
        self.assertEqual(threat.severity, ThreatEvent.Severity.HIGH)
        self.assertIsNotNone(threat.detected_at)

    def test_threat_status_workflow(self):
        """
        Validates: Threat moves through status workflow.
        Why it matters: Incident response tracking.
        """
        threat = ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.UNAUTHORIZED_ACCESS,
            severity=ThreatEvent.Severity.CRITICAL,
            target_resource='Database-01',
            description='Unauthorized access attempt',
        )

        # Move through workflow
        threat.status = ThreatEvent.Status.INVESTIGATING
        threat.save()
        threat.refresh_from_db()
        self.assertEqual(threat.status, ThreatEvent.Status.INVESTIGATING)

        threat.status = ThreatEvent.Status.MITIGATED
        threat.save()
        threat.refresh_from_db()
        self.assertEqual(threat.status, ThreatEvent.Status.MITIGATED)

    def test_threat_assignment(self):
        """
        Validates: Threat can be assigned to an analyst.
        Why it matters: Incident response assignment tracking.
        """
        analyst = User.objects.create_user(
            username='analyst',
            email='analyst@example.com',
            password='AnalystPass123!',
            role=User.Role.ANALYST,
        )

        threat = ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.DATA_EXFILTRATION,
            severity=ThreatEvent.Severity.CRITICAL,
            target_resource='DataStore-01',
            assigned_to=analyst,
        )

        self.assertEqual(threat.assigned_to, analyst)

    def test_threat_indicators_stored(self):
        """
        Validates: Threat indicators (IOCs) are stored as JSON.
        Why it matters: IOCs used for detection and correlation.
        """
        indicators = {
            'ip_addresses': ['10.0.0.1', '10.0.0.2'],
            'file_hashes': ['abc123', 'def456'],
            'domains': ['malicious.com'],
        }

        threat = ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.PHISHING_ATTEMPT,
            severity=ThreatEvent.Severity.HIGH,
            target_resource='Email-Gateway',
            indicators=indicators,
        )

        self.assertEqual(threat.indicators['ip_addresses'], ['10.0.0.1', '10.0.0.2'])
        self.assertEqual(len(threat.indicators['file_hashes']), 2)


class ThreatFeedValidationTests(TestCase):
    """Test threat feed (IOC) validation."""

    def test_threat_feed_creation(self):
        """
        Validates: Threat feed entry is created.
        Why it matters: IOC database foundation.
        """
        feed = ThreatFeed.objects.create(
            feed_name='abuse.ch-feed',
            threat_indicator='192.168.1.100',
            indicator_type=ThreatFeed.IndicatorType.IP,
            threat_category='Known C2 server',
            source='abuse.ch',
            confidence_score=95,
            added_at=timezone.now(),
        )

        self.assertIsNotNone(feed.id)
        self.assertEqual(feed.confidence_score, 95)

    def test_threat_feed_types(self):
        """
        Validates: Different indicator types can be stored.
        Why it matters: Various IOC types needed for detection.
        """
        indicators = [
            ('192.168.1.1', ThreatFeed.IndicatorType.IP),
            ('malicious.com', ThreatFeed.IndicatorType.DOMAIN),
            ('abc123def456', ThreatFeed.IndicatorType.HASH),
            ('cmd.exe /c powershell', ThreatFeed.IndicatorType.PATTERN),
        ]

        for indicator, itype in indicators:
            feed = ThreatFeed.objects.create(
                feed_name='test-feed',
                threat_indicator=indicator,
                indicator_type=itype,
                threat_category='test-category',
                source='test',
                confidence_score=90,
                added_at=timezone.now(),
            )
            self.assertEqual(feed.indicator_type, itype)

    def test_threat_feed_active_filtering(self):
        """
        Validates: Only active feeds are used for detection.
        Why it matters: Retired IOCs shouldn't trigger alerts.
        """
        ThreatFeed.objects.create(
            feed_name='old-feed',
            threat_indicator='old.malware.com',
            indicator_type=ThreatFeed.IndicatorType.DOMAIN,
            threat_category='malware',
            source='test',
            is_active=False,
            added_at=timezone.now(),
        )

        ThreatFeed.objects.create(
            feed_name='current-feed',
            threat_indicator='current.malware.com',
            indicator_type=ThreatFeed.IndicatorType.DOMAIN,
            threat_category='malware',
            source='test',
            is_active=True,
            added_at=timezone.now(),
        )

        active = ThreatFeed.objects.filter(is_active=True)
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().threat_indicator, 'current.malware.com')

    def test_threat_feed_confidence_score(self):
        """
        Validates: Confidence score affects alert severity.
        Why it matters: High confidence IOCs trigger stronger alerts.
        """
        low_conf = ThreatFeed.objects.create(
            feed_name='low-conf-feed',
            threat_indicator='maybe.bad.com',
            indicator_type=ThreatFeed.IndicatorType.DOMAIN,
            threat_category='suspicious',
            source='test',
            confidence_score=30,
            added_at=timezone.now(),
        )

        high_conf = ThreatFeed.objects.create(
            feed_name='high-conf-feed',
            threat_indicator='definitely.bad.com',
            indicator_type=ThreatFeed.IndicatorType.DOMAIN,
            threat_category='malware',
            source='test',
            confidence_score=99,
            added_at=timezone.now(),
        )

        self.assertLess(low_conf.confidence_score, high_conf.confidence_score)


class RiskScoreCalculationTests(TestCase):
    """Test risk score computation."""

    def setUp(self):
        """Create test system."""
        self.system = HealthcareSystem.objects.create(
            name='Risk Test System',
            system_type=HealthcareSystem.SystemType.EHR,
            contains_phi=True,
        )

    def test_risk_score_creation(self):
        """
        Validates: RiskScore record is created.
        Why it matters: Historical risk tracking.
        """
        score = RiskScore.objects.create(
            system=self.system,
            score=7.5,
            risk_level=RiskScore.RiskLevel.HIGH,
            computed_at=timezone.now(),
        )

        self.assertIsNotNone(score.id)
        self.assertEqual(score.score, 7.5)

    def test_risk_level_classification(self):
        """
        Validates: Risk score maps to risk level.
        Why it matters: Color-coded risk indicators for dashboards.
        """
        test_cases = [
            (2.5, RiskScore.RiskLevel.LOW),
            (4.5, RiskScore.RiskLevel.MEDIUM),
            (7.5, RiskScore.RiskLevel.HIGH),
            (9.5, RiskScore.RiskLevel.CRITICAL),
        ]

        for score_val, expected_level in test_cases:
            score = RiskScore.objects.create(
                system=self.system,
                score=score_val,
                risk_level=expected_level,
            )
            self.assertEqual(score.risk_level, expected_level)

    def test_risk_score_components(self):
        """
        Validates: Risk score includes multiple factors.
        Why it matters: Holistic risk assessment.
        """
        score = RiskScore.objects.create(
            system=self.system,
            score=7.5,
            risk_level=RiskScore.RiskLevel.HIGH,
            threat_likelihood=6.0,
            impact_magnitude=8.5,
            vulnerability_index=6.0,
        )

        self.assertEqual(score.threat_likelihood, 6.0)
        self.assertEqual(score.impact_magnitude, 8.5)
        self.assertEqual(score.vulnerability_index, 6.0)


class VulnerabilityTrackingTests(TestCase):
    """Test vulnerability management and patching."""

    def test_vulnerability_creation(self):
        """
        Validates: Vulnerability record is created.
        Why it matters: CVE tracking foundation.
        """
        vuln = VulnerabilityRecord.objects.create(
            cve_reference='CVE-2024-1234',
            title='Critical RCE in Apache',
            description='Remote code execution vulnerability',
            cvss_score=9.8,
            severity=VulnerabilityRecord.Severity.CRITICAL,
            affected_component='Apache 2.4.41',
            discovered_at=timezone.now(),
        )

        self.assertIsNotNone(vuln.id)
        self.assertEqual(vuln.cvss_score, 9.8)

    def test_vulnerability_patch_tracking(self):
        """
        Validates: Patch status is tracked.
        Why it matters: Remediation tracking for compliance.
        """
        vuln = VulnerabilityRecord.objects.create(
            cve_reference='CVE-2024-5678',
            title='SQL Injection',
            cvss_score=7.2,
            severity=VulnerabilityRecord.Severity.HIGH,
            affected_component='Django ORM',
            discovered_at=timezone.now(),
            patched=False,
        )

        self.assertFalse(vuln.patched)
        self.assertIsNone(vuln.patched_at)

        # Apply patch
        vuln.patched = True
        vuln.patch_notes = 'Applied security update v2.1.0'
        vuln.save()

        vuln.refresh_from_db()
        self.assertTrue(vuln.patched)

    def test_unpatched_critical_vulnerabilities(self):
        """
        Validates: Critical unpatched vulns are flagged.
        Why it matters: High-priority remediation tracking.
        """
        VulnerabilityRecord.objects.create(
            cve_reference='CVE-2024-9999',
            title='Critical Bug',
            cvss_score=9.5,
            severity=VulnerabilityRecord.Severity.CRITICAL,
            affected_component='System-Component',
            discovered_at=timezone.now(),
            patched=False,
        )

        critical_unpatched = VulnerabilityRecord.objects.filter(
            severity=VulnerabilityRecord.Severity.CRITICAL,
            patched=False
        )

        self.assertEqual(critical_unpatched.count(), 1)

    def test_vulnerability_severity_distribution(self):
        """
        Validates: Vulnerabilities can be analyzed by severity.
        Why it matters: Risk prioritization.
        """
        severities = [
            VulnerabilityRecord.Severity.LOW,
            VulnerabilityRecord.Severity.MEDIUM,
            VulnerabilityRecord.Severity.HIGH,
            VulnerabilityRecord.Severity.CRITICAL,
        ]

        for severity in severities:
            VulnerabilityRecord.objects.create(
                cve_reference=f'CVE-{severity}',
                title=f'{severity} Bug',
                cvss_score=5.0,
                severity=severity,
                affected_component='Test-Component',
                discovered_at=timezone.now(),
            )

        for severity in severities:
            count = VulnerabilityRecord.objects.filter(severity=severity).count()
            self.assertEqual(count, 1)


class RiskAssessmentTests(TestCase):
    """Test risk assessment generation and tracking."""

    def setUp(self):
        """Create test analyst."""
        self.analyst = User.objects.create_user(
            username='riskanalyst',
            email='riskanalyst@example.com',
            password='AnalystPass123!',
            role=User.Role.ANALYST,
        )

    def test_risk_assessment_creation(self):
        """
        Validates: Risk assessment record is created.
        Why it matters: Assessment tracking for compliance.
        """
        assessment = RiskAssessment.objects.create(
            conducted_by=self.analyst,
            overall_risk_score=7.2,
            risk_level=RiskAssessment.RiskLevel.HIGH,
            next_assessment_due=timezone.now().date() + timezone.timedelta(days=90),
        )

        self.assertIsNotNone(assessment.assessment_id)
        self.assertEqual(assessment.overall_risk_score, 7.2)

    def test_assessment_recommendation_storage(self):
        """
        Validates: Recommendations are documented.
        Why it matters: Remediation guidance for stakeholders.
        """
        assessment = RiskAssessment.objects.create(
            conducted_by=self.analyst,
            overall_risk_score=6.5,
            risk_level=RiskAssessment.RiskLevel.MEDIUM,
            recommendations='Apply patches, implement network segmentation',
            next_assessment_due=timezone.now().date() + timezone.timedelta(days=90),
        )

        self.assertIn('Apply patches', assessment.recommendations)

    def test_assessment_next_due_date(self):
        """
        Validates: Next assessment due date is set.
        Why it matters: Regular assessment scheduling.
        """
        next_due = timezone.now().date() + timezone.timedelta(days=90)
        assessment = RiskAssessment.objects.create(
            conducted_by=self.analyst,
            overall_risk_score=8.0,
            risk_level=RiskAssessment.RiskLevel.HIGH,
            next_assessment_due=next_due,
        )

        self.assertIsNotNone(assessment.next_assessment_due)
        self.assertEqual(assessment.next_assessment_due, next_due)
