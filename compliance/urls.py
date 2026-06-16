"""compliance/urls.py – URL patterns for the compliance management module."""

from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    # New compliance engine views
    path('', views.compliance_dashboard, name='dashboard'),
    path('controls/', views.control_list, name='control_list'),
    path('check/run/', views.run_compliance_check, name='run_check'),
    path('remediation/', views.remediation_view, name='remediation'),
    path('reports/', views.compliance_reports, name='reports'),

    # Legacy aliases (kept so existing sidebar links / tests don't break)
    path('summary/', views.compliance_summary, name='summary'),
    path('frameworks/', views.framework_list, name='framework_list'),
    path('frameworks/<int:pk>/', views.framework_detail, name='framework_detail'),
    path('controls/<int:pk>/', views.control_detail, name='control_detail'),
]
