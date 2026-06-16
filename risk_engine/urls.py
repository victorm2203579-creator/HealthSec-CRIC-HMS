"""risk_engine/urls.py – HTML URL patterns for risk intelligence."""

from django.urls import path
from . import views

app_name = 'risk_engine'

urlpatterns = [
    # Dashboard & legacy score
    path('', views.risk_dashboard, name='risk_dashboard'),
    path('compute/<int:system_pk>/', views.compute_risk_score, name='compute_risk_score'),

    # Threat events
    path('threats/', views.threat_event_list, name='threat_event_list'),
    path('threats/<int:pk>/', views.threat_event_detail, name='threat_event_detail'),

    # Vulnerabilities
    path('vulnerabilities/', views.vulnerability_list, name='vulnerability_list'),
    path('vulnerabilities/<int:pk>/patch/', views.mark_patched, name='mark_patched'),

    # Risk assessments
    path('assessment/', views.risk_assessment, name='risk_assessment'),
    path('assessment/generate/', views.generate_assessment, name='generate_assessment'),
]
