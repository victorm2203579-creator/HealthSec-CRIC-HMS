"""
accounts/models.py
==================
Custom User model and UserProfile for the HealthSec system.

Role hierarchy (lowest → highest privilege):
  VIEWER      Read-only access to dashboards and reports.
  ANALYST     Can review alerts and run compliance checks.
  COMPLIANCE  Manages compliance frameworks and controls.
  ADMIN       Full system access including user management.

Using a custom User model (AbstractUser) gives us full control over
authentication fields without breaking Django's built-in auth system.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended Django user with role-based access control."""

    class Role(models.TextChoices):
        VIEWER = 'VIEWER', _('Viewer')
        ANALYST = 'ANALYST', _('Analyst')
        COMPLIANCE = 'COMPLIANCE', _('Compliance Officer')
        ADMIN = 'ADMIN', _('Administrator')

    # Override email to be unique and required (used as display identifier)
    email = models.EmailField(_('email address'), unique=True)

    # Role that drives permission checks across the entire system
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
    )

    # Profile picture stored in media/avatars/
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
    )

    # Department / organisational unit (e.g. "ICT", "Clinical Informatics")
    department = models.CharField(max_length=100, blank=True)

    # Phone number for out-of-band alert notifications
    phone_number = models.CharField(max_length=20, blank=True)

    # Force password change on first login (new accounts)
    must_change_password = models.BooleanField(default=True)

    # Track the last IP address that logged in (for audit purposes)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    # --- Convenience permission helpers ---

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_compliance_officer(self) -> bool:
        return self.role in (self.Role.COMPLIANCE, self.Role.ADMIN) or self.is_superuser

    @property
    def is_analyst(self) -> bool:
        return self.role in (
            self.Role.ANALYST, self.Role.COMPLIANCE, self.Role.ADMIN
        ) or self.is_superuser

    def get_role_badge_class(self) -> str:
        """Return a Bootstrap badge CSS class matching the user's role."""
        mapping = {
            self.Role.VIEWER: 'secondary',
            self.Role.ANALYST: 'info',
            self.Role.COMPLIANCE: 'warning',
            self.Role.ADMIN: 'danger',
        }
        return mapping.get(self.role, 'secondary')


class UserProfile(models.Model):
    """
    Extra profile data for each user.
    Kept separate from User so the core auth table stays lean.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )

    # Biography or position description shown on the profile page
    bio = models.TextField(blank=True)

    # Whether the user wants to receive email alerts
    email_notifications = models.BooleanField(default=True)

    # Number of consecutive failed login attempts (reset on success)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)

    # Timestamp of last failed login (used for lockout duration)
    last_failed_login = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user_profile'
        verbose_name = 'User Profile'

    def __str__(self):
        return f'Profile – {self.user.username}'


class LoginHistory(models.Model):
    """Track user login attempts with IP, location, and device info."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history',
    )

    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500, blank=True)
    device_info = models.CharField(max_length=200, blank=True)

    # GeoIP location data
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Risk assessment
    is_suspicious = models.BooleanField(default=False)
    suspicious_reason = models.CharField(max_length=500, blank=True)
    risk_score = models.PositiveSmallIntegerField(default=0)

    # Status
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=200, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'accounts_login_history'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['is_suspicious', '-timestamp']),
            models.Index(fields=['country_code', '-timestamp']),
        ]

    def __str__(self):
        location = f"{self.city}, {self.country}" if self.city else self.country or "Unknown"
        return f"{self.user.username} @ {location} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class TwoFactorAuth(models.Model):
    """TOTP-based two-factor authentication configuration."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='totp_auth',
    )

    secret_key = models.CharField(max_length=32)  # Base32 encoded TOTP secret

    is_enabled = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # Verified with test code

    backup_codes = models.JSONField(default=list, blank=True)  # List of one-time codes

    created_at = models.DateTimeField(auto_now_add=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'accounts_two_factor_auth'
        verbose_name = 'Two Factor Authentication'
        verbose_name_plural = 'Two Factor Authentications'

    def __str__(self):
        status = "Enabled" if self.is_enabled else "Disabled"
        return f"2FA for {self.user.username} ({status})"
