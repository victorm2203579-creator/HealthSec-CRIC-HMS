"""monitoring/urls.py – HTML view URL patterns for the monitoring app."""

from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # --- Existing infrastructure views ---
    path('', views.system_list, name='system_list'),
    path('systems/<int:pk>/', views.system_detail, name='system_detail'),
    path('events/', views.event_list, name='event_list'),

    # --- Monitoring dashboard ---
    path('dashboard/', views.monitoring_dashboard, name='monitoring_dashboard'),

    # --- Suspicious activity ---
    path('suspicious/', views.suspicious_activity_list, name='suspicious_activity_list'),
    path('suspicious/<int:pk>/resolve/', views.resolve_suspicious, name='resolve_suspicious'),
]
