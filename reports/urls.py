"""reports/urls.py – URL patterns for PDF reports."""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('generate/risk/', views.generate_risk_report, name='generate_risk'),
    path('generate/compliance/<int:framework_pk>/', views.generate_compliance_report, name='generate_compliance'),
]
