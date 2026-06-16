"""
accounts/totp_service.py
=======================
TOTP-based two-factor authentication service.

Uses pyotp library to generate and verify time-based one-time passwords (TOTP).
Compatible with Google Authenticator, Authy, Microsoft Authenticator.
"""

import logging
import qrcode
import io
import base64
from django.conf import settings
from django.utils import timezone

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class TOTPService:
    """Service for TOTP-based 2FA management."""

    @staticmethod
    def generate_secret():
        """
        Generate a new random TOTP secret key.

        Returns:
            str: Base32-encoded random secret (for QR code generation)
        """
        if not PYOTP_AVAILABLE:
            raise ImportError("pyotp library not installed")

        return pyotp.random_base32()

    @staticmethod
    def get_totp(secret):
        """
        Get TOTP object from secret key.

        Args:
            secret (str): Base32-encoded secret

        Returns:
            pyotp.TOTP: TOTP object for generating codes
        """
        if not PYOTP_AVAILABLE:
            raise ImportError("pyotp library not installed")

        return pyotp.TOTP(secret)

    @staticmethod
    def get_current_code(secret):
        """
        Get the current valid TOTP code.

        Args:
            secret (str): Base32-encoded secret

        Returns:
            str: 6-digit TOTP code
        """
        totp = TOTPService.get_totp(secret)
        return totp.now()

    @staticmethod
    def verify_code(secret, code, time_window=1):
        """
        Verify a TOTP code.

        Args:
            secret (str): Base32-encoded secret
            code (str): 6-digit code to verify
            time_window (int): Allow codes from N time windows ago (default 1 = 30 seconds)

        Returns:
            bool: True if code is valid
        """
        totp = TOTPService.get_totp(secret)
        # Allow code from current and previous time window for clock skew
        return totp.verify(code, valid_window=time_window)

    @staticmethod
    def generate_qr_code(secret, user_email, issuer_name="HealthSec"):
        """
        Generate a QR code for TOTP setup.

        Args:
            secret (str): Base32-encoded secret
            user_email (str): User email for display in authenticator
            issuer_name (str): Issuer name shown in authenticator

        Returns:
            str: Base64-encoded PNG image data for <img src="data:image/png;base64,...">
        """
        totp = TOTPService.get_totp(secret)
        totp.name = user_email
        totp.issuer_name = issuer_name

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp.provisioning_uri(name=user_email, issuer_name=issuer_name))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 PNG
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_image = base64.b64encode(buffer.getvalue()).decode()

        return qr_image

    @staticmethod
    def generate_backup_codes(count=10):
        """
        Generate one-time backup codes for account recovery.

        Args:
            count (int): Number of codes to generate

        Returns:
            list: List of 8-character alphanumeric codes
        """
        import secrets
        import string

        chars = string.ascii_uppercase + string.digits
        codes = ['-'.join(secrets.token_urlsafe(4) for _ in range(2)) for _ in range(count)]
        return codes

    @staticmethod
    def use_backup_code(backup_codes, code):
        """
        Use a backup code (removes it from list).

        Args:
            backup_codes (list): List of available backup codes
            code (str): Code to use

        Returns:
            tuple: (success: bool, remaining: list)
        """
        code = code.upper().replace(' ', '')

        if code in backup_codes:
            backup_codes.remove(code)
            return True, backup_codes

        return False, backup_codes

    @staticmethod
    def enforce_2fa_for_role(user):
        """
        Check if user's role requires 2FA.

        Args:
            user: User model instance

        Returns:
            bool: True if 2FA is required
        """
        return user.role in [
            user.Role.ADMIN,
            user.Role.ANALYST,
            user.Role.COMPLIANCE,
        ]


def get_totp_service():
    """Get TOTP service (for compatibility)."""
    return TOTPService
