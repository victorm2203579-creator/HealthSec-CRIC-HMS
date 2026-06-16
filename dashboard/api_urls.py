"""dashboard/api_urls.py – REST API URLs for dashboard endpoints."""

from django.urls import path
from .views import (
    DashboardAPIView,
    ThreatTimelineAPIView,
    ComplianceBreakdownAPIView,
    RiskHeatmapAPIView,
    SeverityDistributionAPIView,
)

app_name = 'dashboard_api'

urlpatterns = [
    path('stats/', DashboardAPIView.as_view(), name='stats'),
    path('threat-timeline/', ThreatTimelineAPIView.as_view(), name='threat_timeline'),
    path('compliance-breakdown/', ComplianceBreakdownAPIView.as_view(), name='compliance_breakdown'),
    path('risk-heatmap/', RiskHeatmapAPIView.as_view(), name='risk_heatmap'),
    path('severity-distribution/', SeverityDistributionAPIView.as_view(), name='severity_distribution'),
]
