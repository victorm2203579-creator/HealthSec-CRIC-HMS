"""audit/apps.py – App configuration for the audit logging subsystem."""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Audit Log'

    def ready(self):
        """Register signal handlers when the app is ready."""
        import audit.signals
