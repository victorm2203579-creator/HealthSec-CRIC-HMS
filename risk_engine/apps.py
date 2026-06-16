"""risk_engine/apps.py – App configuration for the cyber risk intelligence engine."""

from django.apps import AppConfig


class RiskEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'risk_engine'
    verbose_name = 'Cyber Risk Intelligence Engine'
