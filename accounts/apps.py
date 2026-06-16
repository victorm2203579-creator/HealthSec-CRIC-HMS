"""
accounts/apps.py
================
App configuration for the accounts app.
Imports signals when Django is ready so user profile creation fires automatically.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'User Accounts & Roles'

    def ready(self):
        # Register signal handlers (e.g., auto-create Profile on User save)
        import accounts.signals  # noqa: F401
