"""alerts/urls.py – URL patterns for alerts and incidents."""

from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('dashboard/', views.alert_dashboard, name='dashboard'),
    path('', views.alert_list, name='alert_list'),
    path('<uuid:pk>/', views.alert_detail, name='alert_detail'),
    path('api/unread/', views.unread_alerts_count, name='api_unread_count'),
    path('mark-all-read/', views.mark_all_alerts_read, name='mark_all_read'),
    path('test-email/', views.test_email, name='test_email'),
    path('incidents/', views.incident_list, name='incident_list'),
    path('incidents/create/', views.incident_create, name='incident_create'),
    path('incidents/<uuid:pk>/', views.incident_detail, name='incident_detail'),
]
