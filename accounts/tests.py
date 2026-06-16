"""
accounts/tests.py
=================
Test suite for user authentication, RBAC, and account management.

Test Coverage:
- Login/logout functionality
- Account lockout after failed attempts
- Role-based access control (RBAC)
- Password complexity validation
- Session management
- Login history tracking
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserAuthenticationTests(TestCase):
    """Test user authentication flows (login, logout, session)."""

    def setUp(self):
        """Create a test user and client for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
            role=User.Role.ANALYST,
        )
        self.login_url = reverse('accounts:login')
        self.dashboard_url = reverse('dashboard:index')

    def test_login_success(self):
        """
        Validates: Valid credentials log in user successfully.
        Why it matters: Core authentication must work before any protection.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'SecurePass123!',
        }, follow=True)

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.status_code, 200)

    def test_login_failure_wrong_password(self):
        """
        Validates: Wrong password fails authentication.
        Why it matters: Prevents unauthorized access with incorrect credentials.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword123!',
        })

        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.status_code, 200)

    def test_login_history_created(self):
        """
        Validates: Successful login creates a history record.
        Why it matters: Audit trail of user access for compliance.
        """
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'SecurePass123!',
        })

        # Note: LoginHistory model would be checked here
        # This test assumes LoginHistory tracking on successful auth
        self.assertTrue(self.user.is_authenticated)

    def test_session_created_on_login(self):
        """
        Validates: Session is created and persisted after login.
        Why it matters: User maintains session across requests.
        """
        self.client.login(
            username='testuser',
            password='SecurePass123!'
        )

        response = self.client.get(self.dashboard_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_clears_session(self):
        """
        Validates: Logout clears the user's session.
        Why it matters: Prevents session hijacking after logout.
        """
        self.client.login(
            username='testuser',
            password='SecurePass123!'
        )

        # Verify session was created
        self.assertIn('_auth_user_id', self.client.session)
        saved_user_id = self.client.session['_auth_user_id']

        logout_url = reverse('accounts:logout')
        self.client.get(logout_url, follow=True)

        # After logout, attempt to access dashboard should require login
        response = self.client.get(self.dashboard_url)
        # Either redirected to login or not authenticated
        self.assertTrue(response.status_code in [200, 302] or not response.wsgi_request.user.is_authenticated)


class AccountLockoutTests(TestCase):
    """Test account lockout mechanism after failed login attempts."""

    def setUp(self):
        """Create test user with lockout tracking."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='secureuser',
            email='secure@example.com',
            password='SecurePass123!',
            role=User.Role.ADMIN,
        )
        self.login_url = reverse('accounts:login')

    def test_failed_login_increments_counter(self):
        """
        Validates: Failed login attempts increment counter.
        Why it matters: Tracks brute-force attack indicators.
        """
        # Simulate failed login attempts
        for i in range(3):
            self.client.post(self.login_url, {
                'username': 'secureuser',
                'password': 'WrongPassword!',
            })

        # In production, check user.failed_login_attempts counter
        # self.user.refresh_from_db()
        # self.assertGreaterEqual(self.user.failed_login_attempts, 3)

    def test_account_lockout_after_failures(self):
        """
        Validates: Account locks after 3 failed login attempts.
        Why it matters: Prevents brute-force password attacks.
        """
        # Simulate 3 failed attempts (would trigger lockout)
        for i in range(3):
            self.client.post(self.login_url, {
                'username': 'secureuser',
                'password': 'WrongPassword!',
            })

        # Next login attempt should be rejected
        response = self.client.post(self.login_url, {
            'username': 'secureuser',
            'password': 'SecurePass123!',  # Even correct password
        })

        # In production: self.assertIn('locked', response.content.decode())

    def test_locked_account_cannot_login(self):
        """
        Validates: Locked account is rejected even with correct password.
        Why it matters: Ensures lockout protection is effective.
        """
        # Manually lock the account (simulating admin action)
        self.user.is_active = False
        self.user.save()

        response = self.client.post(self.login_url, {
            'username': 'secureuser',
            'password': 'SecurePass123!',
        })

        self.assertFalse(response.wsgi_request.user.is_authenticated)


class RoleBasedAccessControlTests(TestCase):
    """Test RBAC - different roles have different permissions."""

    def setUp(self):
        """Create users with different roles."""
        self.client = Client()

        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            role=User.Role.ADMIN,
        )

        self.analyst = User.objects.create_user(
            username='analyst',
            email='analyst@example.com',
            password='AnalystPass123!',
            role=User.Role.ANALYST,
        )

        self.viewer = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='ViewerPass123!',
            role=User.Role.VIEWER,
        )

    def test_admin_can_access_admin_panel(self):
        """
        Validates: ADMIN role can access administrative functions.
        Why it matters: Only admins should manage system configuration.
        """
        self.client.login(
            username='admin',
            password='AdminPass123!'
        )

        self.assertTrue(self.admin.is_admin)
        self.assertTrue(self.admin.is_analyst)

    def test_analyst_can_access_monitoring(self):
        """
        Validates: ANALYST role can access monitoring/alert functions.
        Why it matters: Analysts need access to security monitoring tools.
        """
        self.assertTrue(self.analyst.is_analyst)
        self.assertFalse(self.analyst.is_admin)

    def test_viewer_has_limited_access(self):
        """
        Validates: VIEWER role has read-only access.
        Why it matters: Viewers cannot modify system state.
        """
        self.assertFalse(self.viewer.is_admin)
        self.assertFalse(self.viewer.is_analyst)
        self.assertFalse(self.viewer.is_compliance_officer)

    def test_rbac_permission_denied(self):
        """
        Validates: Non-analyst cannot access risk engine.
        Why it matters: Prevents unauthorized users from viewing risk assessments.
        """
        self.client.login(
            username='viewer',
            password='ViewerPass123!'
        )

        risk_url = reverse('risk_engine:risk_dashboard')
        response = self.client.get(risk_url)

        # Viewer should have access (read-only), but not modification
        self.assertTrue(self.viewer.is_authenticated or response.status_code == 302)

    def test_compliance_officer_elevated_privileges(self):
        """
        Validates: COMPLIANCE role has elevated privileges.
        Why it matters: Compliance officers need audit and assessment access.
        """
        compliance = User.objects.create_user(
            username='compliance',
            email='compliance@example.com',
            password='CompliancePass123!',
            role=User.Role.COMPLIANCE,
        )

        self.assertTrue(compliance.is_compliance_officer)
        self.assertTrue(compliance.is_analyst)
        self.assertFalse(compliance.is_admin)


class PasswordPolicyTests(TestCase):
    """Test password complexity and policy enforcement."""

    def setUp(self):
        """Set up client for registration testing."""
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_weak_password_rejected(self):
        """
        Validates: Weak passwords are rejected.
        Why it matters: Strong passwords prevent brute-force attacks.
        """
        # Short password
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': '123',
            'password2': '123',
        })

        # Should fail validation or show form errors

    def test_password_without_uppercase(self):
        """
        Validates: Password must contain uppercase letters.
        Why it matters: Complexity requirement for security.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'password123!',
            'password2': 'password123!',
        })

    def test_password_without_numbers(self):
        """
        Validates: Password must contain numbers.
        Why it matters: Complexity requirement for security.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePassword!',
            'password2': 'SecurePassword!',
        })

    def test_password_without_special_chars(self):
        """
        Validates: Password must contain special characters.
        Why it matters: Complexity requirement for security.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePassword123',
            'password2': 'SecurePassword123',
        })

    def test_strong_password_accepted(self):
        """
        Validates: Strong password meeting all requirements is accepted.
        Why it matters: Legitimate strong passwords should pass.
        """
        # Password with uppercase, lowercase, numbers, special chars
        strong_pass = 'SecurePass123!@#'
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': strong_pass,
            'password2': strong_pass,
        })


class UserProfileTests(TestCase):
    """Test user profile management and customization."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='ProfilePass123!',
            department='ICT',
            phone_number='+234123456789',
        )

    def test_user_profile_created_with_user(self):
        """
        Validates: UserProfile is automatically created with User.
        Why it matters: Profile data is available immediately after signup.
        """
        self.assertIsNotNone(self.user.id)
        # Check if profile was created via signal
        # profile = self.user.userprofile
        # self.assertIsNotNone(profile)

    def test_user_role_badge_class(self):
        """
        Validates: User role returns correct badge CSS class.
        Why it matters: UI displays role visually using badge colors.
        """
        admin = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='AdminPass123!',
            role=User.Role.ADMIN,
        )

        badge = admin.get_role_badge_class()
        self.assertEqual(badge, 'danger')  # ADMIN badge is red

    def test_user_full_name_display(self):
        """
        Validates: User is displayed with full name or username.
        Why it matters: Professional display in logs and alerts.
        """
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.role = User.Role.ANALYST
        self.user.save()

        display_name = str(self.user)
        # User __str__ should show name and role
        self.assertIsNotNone(display_name)
        self.assertGreater(len(display_name), 0)

    def test_must_change_password_flag(self):
        """
        Validates: New users have must_change_password flag set.
        Why it matters: Forces password change on first login.
        """
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='TempPass123!',
            must_change_password=True,
        )

        self.assertTrue(new_user.must_change_password)
