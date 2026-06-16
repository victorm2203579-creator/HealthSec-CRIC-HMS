"""audit/urls.py – URL patterns for audit logging and integrity verification."""

from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.audit_log_list, name='log_list'),
    path('export/', views.export_audit_logs, name='export'),
    path('<uuid:log_id>/', views.audit_log_detail, name='log_detail'),
    path('integrity/', views.integrity_check, name='integrity_check'),
    path('report/', views.audit_report, name='report'),
]
