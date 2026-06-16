"""alerts/apps.py – App configuration for alerts and incident response."""

from django.apps import AppConfig


class AlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alerts'
    verbose_name = 'Alerts & Incident Response'

    def ready(self):
        import alerts.signals
