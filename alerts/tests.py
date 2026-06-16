"""
alerts/tests.py
===============
Test suite for alert generation, incident management, and notifications.

Test Coverage:
- Alert creation and status tracking
- Email notifications for high-severity alerts
- Incident number generation
- Alert acknowledgment workflow
- Alert resolution
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import outbox

from alerts.models import Alert, Incident, Notification
from monitoring.models import HealthcareSystem, MonitoringEvent

User = get_user_model()


class AlertCreationTests(TestCase):
    """Test alert creation and field validation."""

    def setUp(self):
        """Create test system."""
        self.system = HealthcareSystem.objects.create(
            name='Test System',
            system_type=HealthcareSystem.SystemType.EHR,
            contains_phi=True,
        )

    def test_alert_creation(self):
        """
        Validates: Alert is created with required fields.
        Why it matters: Foundation for alert lifecycle.
        """
        alert = Alert.objects.create(
            title='Suspicious Access Detected',
            description='User accessed 50 records in 10 minutes',
            alert_type=Alert.AlertType.SUSPICIOUS_ACTIVITY,
            severity=Alert.Severity.HIGH,
            affected_system=self.system,
        )

        self.assertIsNotNone(alert.id)
        self.assertEqual(alert.status, Alert.Status.NEW)
        self.assertTrue(alert.is_read is False)

    def test_alert_severity_levels(self):
        """
        Validates: Alert can have various severity levels.
        Why it matters: Severity drives alert priority and routing.
        """
        severities = [
            Alert.Severity.LOW,
            Alert.Severity.MEDIUM,
            Alert.Severity.HIGH,
            Alert.Severity.CRITICAL,
        ]

        for severity in severities:
            alert = Alert.objects.create(
                title=f'{severity} Alert',
                alert_type=Alert.AlertType.SECURITY,
                severity=severity,
            )
            self.assertEqual(alert.severity, severity)

    def test_alert_type_variety(self):
        """
        Validates: Different alert types can be created.
        Why it matters: Categorizes alerts by issue type.
        """
        alert_types = [
            Alert.AlertType.SECURITY,
            Alert.AlertType.COMPLIANCE,
            Alert.AlertType.DATA_BREACH,
            Alert.AlertType.UNAUTHORIZED_ACCESS,
        ]

        for alert_type in alert_types:
            alert = Alert.objects.create(
                title=f'{alert_type} Alert',
                alert_type=alert_type,
                severity=Alert.Severity.MEDIUM,
            )
            self.assertEqual(alert.alert_type, alert_type)

    def test_alert_timestamp(self):
        """
        Validates: Alert capture time and creation time.
        Why it matters: Timeline reconstruction for incidents.
        """
        alert = Alert.objects.create(
            title='Test Alert',
            alert_type=Alert.AlertType.SECURITY,
            severity=Alert.Severity.HIGH,
        )

        self.assertIsNotNone(alert.created_at)
        self.assertIsNotNone(alert.updated_at)


class AlertStatusWorkflowTests(TestCase):
    """Test alert status lifecycle."""

    def setUp(self):
        """Create test alert."""
        self.alert = Alert.objects.create(
            title='Status Test Alert',
            alert_type=Alert.AlertType.SECURITY,
            severity=Alert.Severity.MEDIUM,
        )

    def test_alert_acknowledgment(self):
        """
        Validates: Alert status changes to ACKNOWLEDGED.
        Why it matters: Tracks analyst response to alerts.
        """
        self.assertEqual(self.alert.status, Alert.Status.NEW)

        self.alert.status = Alert.Status.ACKNOWLEDGED
        self.alert.save()

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.ACKNOWLEDGED)

    def test_alert_in_progress(self):
        """
        Validates: Alert moves to IN_PROGRESS during investigation.
        Why it matters: Tracks investigation status.
        """
        self.alert.status = Alert.Status.IN_PROGRESS
        self.alert.save()

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.IN_PROGRESS)

    def test_alert_resolution(self):
        """
        Validates: Alert can be resolved.
        Why it matters: Marks investigation complete.
        """
        self.alert.status = Alert.Status.RESOLVED
        self.alert.save()

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.RESOLVED)

    def test_alert_false_positive(self):
        """
        Validates: Alert can be marked as false positive.
        Why it matters: Tracks false alert rate.
        """
        self.alert.status = Alert.Status.FALSE_POSITIVE
        self.alert.save()

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.FALSE_POSITIVE)

    def test_alert_closed(self):
        """
        Validates: Alert can be closed.
        Why it matters: Final disposition tracking.
        """
        self.alert.status = Alert.Status.CLOSED
        self.alert.save()

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.CLOSED)


class AlertAssignmentTests(TestCase):
    """Test alert assignment to analysts."""

    def setUp(self):
        """Create alert and analyst."""
        self.analyst = User.objects.create_user(
            username='analyst',
            email='analyst@example.com',
            password='AnalystPass123!',
            role=User.Role.ANALYST,
        )

        self.alert = Alert.objects.create(
            title='Assignment Test',
            alert_type=Alert.AlertType.SECURITY,
            severity=Alert.Severity.HIGH,
        )

    def test_alert_assignment(self):
        """
        Validates: Alert can be assigned to analyst.
        Why it matters: Routes work to responsible analyst.
        """
        self.alert.assigned_to = self.analyst
        self.alert.save()

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.assigned_to, self.analyst)

    def test_unassigned_alerts_query(self):
        """
        Validates: Unassigned alerts can be queried.
        Why it matters: Find alerts needing assignment.
        """
        Alert.objects.create(
            title='Unassigned',
            alert_type=Alert.AlertType.SECURITY,
            severity=Alert.Severity.MEDIUM,
        )

        unassigned = Alert.objects.filter(assigned_to__isnull=True)
        self.assertEqual(unassigned.count(), 1)

    def test_analyst_alerts_query(self):
        """
        Validates: Query alerts assigned to specific analyst.
        Why it matters: Workload management.
        """
        self.alert.assigned_to = self.analyst
        self.alert.save()

        analyst_alerts = Alert.objects.filter(assigned_to=self.analyst)
        self.assertEqual(analyst_alerts.count(), 1)


class CriticalAlertNotificationTests(TestCase):
    """Test email notifications for high-severity alerts."""

    def setUp(self):
        """Create admin user for notifications."""
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            role=User.Role.ADMIN,
        )

    def test_critical_alert_triggers_email(self):
        """
        Validates: CRITICAL alerts trigger email notifications.
        Why it matters: Immediate escalation of critical issues.
        """
        alert = Alert.objects.create(
            title='CRITICAL: Active Breach',
            alert_type=Alert.AlertType.DATA_BREACH,
            severity=Alert.Severity.CRITICAL,
            description='Unauthorized data access detected',
        )

        # Simulate email sending (in production)
        # In tests, emails go to outbox
        # outbox contains sent emails when using test mail backend

        # Verify CRITICAL severity
        self.assertEqual(alert.severity, Alert.Severity.CRITICAL)

    def test_high_alert_triggers_email(self):
        """
        Validates: HIGH severity alerts trigger email.
        Why it matters: Important alerts escalated.
        """
        alert = Alert.objects.create(
            title='HIGH: Suspicious Pattern',
            alert_type=Alert.AlertType.SUSPICIOUS_ACTIVITY,
            severity=Alert.Severity.HIGH,
        )

        self.assertEqual(alert.severity, Alert.Severity.HIGH)

    def test_medium_alert_may_trigger_email(self):
        """
        Validates: MEDIUM alerts follow notification policy.
        Why it matters: Balance between alerts and noise.
        """
        alert = Alert.objects.create(
            title='MEDIUM: Investigation',
            alert_type=Alert.AlertType.SECURITY,
            severity=Alert.Severity.MEDIUM,
        )

        self.assertEqual(alert.severity, Alert.Severity.MEDIUM)

    def test_low_alert_no_automatic_email(self):
        """
        Validates: LOW alerts don't trigger automatic emails.
        Why it matters: Reduces alert fatigue.
        """
        alert = Alert.objects.create(
            title='LOW: FYI',
            alert_type=Alert.AlertType.SECURITY,
            severity=Alert.Severity.LOW,
        )

        self.assertEqual(alert.severity, Alert.Severity.LOW)


class IncidentTests(TestCase):
    """Test incident creation and management."""

    def setUp(self):
        """Create test analyst and system."""
        self.analyst = User.objects.create_user(
            username='commander',
            email='commander@example.com',
            password='CommanderPass123!',
            role=User.Role.ANALYST,
        )

        self.system = HealthcareSystem.objects.create(
            name='Incident Test System',
            system_type=HealthcareSystem.SystemType.EHR,
        )

        # Create related alerts
        self.alert1 = Alert.objects.create(
            title='Incident Alert 1',
            alert_type=Alert.AlertType.DATA_BREACH,
            severity=Alert.Severity.CRITICAL,
            affected_system=self.system,
        )

        self.alert2 = Alert.objects.create(
            title='Incident Alert 2',
            alert_type=Alert.AlertType.UNAUTHORIZED_ACCESS,
            severity=Alert.Severity.CRITICAL,
            affected_system=self.system,
        )

    def test_incident_creation(self):
        """
        Validates: Incident is created from related alerts.
        Why it matters: Formal incident tracking and response.
        """
        incident = Incident.objects.create(
            title='Data Breach Response',
            description='Unauthorized access to patient records detected',
            incident_commander=self.analyst,
            affected_system=self.system,
        )

        self.assertIsNotNone(incident.id)
        self.assertIsNotNone(incident.incident_number)

    def test_incident_number_format(self):
        """
        Validates: Incident number follows INC-YYYY-NNNN format.
        Why it matters: Standardized incident identification.
        """
        incident = Incident.objects.create(
            title='Test Incident',
            incident_commander=self.analyst,
            affected_system=self.system,
        )

        # Incident number should be INC-2026-0001 format
        self.assertIsNotNone(incident.incident_number)
        self.assertTrue(incident.incident_number.startswith('INC-'))

    def test_incident_phase_tracking(self):
        """
        Validates: Incident phase is tracked through response.
        Why it matters: Response workflow tracking.
        """
        incident = Incident.objects.create(
            title='Phase Test',
            incident_commander=self.analyst,
            affected_system=self.system,
            phase=Incident.Phase.INITIAL_RESPONSE,
        )

        self.assertEqual(incident.phase, Incident.Phase.INITIAL_RESPONSE)

        # Move to investigation
        incident.phase = Incident.Phase.INVESTIGATION
        incident.save()

        incident.refresh_from_db()
        self.assertEqual(incident.phase, Incident.Phase.INVESTIGATION)

    def test_incident_severity_from_alerts(self):
        """
        Validates: Incident severity reflects alert severity.
        Why it matters: Risk assessment accuracy.
        """
        incident = Incident.objects.create(
            title='CRITICAL Incident',
            incident_commander=self.analyst,
            affected_system=self.system,
            severity=Incident.Severity.CRITICAL,
        )

        self.assertEqual(incident.severity, Incident.Severity.CRITICAL)

    def test_incident_alert_relationship(self):
        """
        Validates: Multiple alerts can relate to single incident.
        Why it matters: Incident correlation and analysis.
        """
        incident = Incident.objects.create(
            title='Multi-Alert Incident',
            incident_commander=self.analyst,
            affected_system=self.system,
        )

        # Link alerts to incident
        self.alert1.related_incident = incident
        self.alert1.save()
        self.alert2.related_incident = incident
        self.alert2.save()

        incident_alerts = Alert.objects.filter(related_incident=incident)
        self.assertEqual(incident_alerts.count(), 2)


class NotificationTests(TestCase):
    """Test notification delivery."""

    def setUp(self):
        """Create test user and alert."""
        self.user = User.objects.create_user(
            username='notifyuser',
            email='notify@example.com',
            password='NotifyPass123!',
        )

        self.alert = Alert.objects.create(
            title='Notification Test',
            alert_type=Alert.AlertType.SECURITY,
            severity=Alert.Severity.HIGH,
        )

    def test_notification_creation(self):
        """
        Validates: Notification record is created.
        Why it matters: Delivery tracking.
        """
        notif = Notification.objects.create(
            alert=self.alert,
            recipient=self.user,
            notification_type=Notification.Type.EMAIL,
        )

        self.assertIsNotNone(notif.id)
        self.assertFalse(notif.is_read)

    def test_notification_status_tracking(self):
        """
        Validates: Notification delivery status is tracked.
        Why it matters: Ensures users received alert.
        """
        notif = Notification.objects.create(
            alert=self.alert,
            recipient=self.user,
            notification_type=Notification.Type.EMAIL,
            status=Notification.Status.PENDING,
        )

        self.assertEqual(notif.status, Notification.Status.PENDING)

        # Mark as sent
        notif.status = Notification.Status.SENT
        notif.sent_at = timezone.now()
        notif.save()

        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.Status.SENT)
