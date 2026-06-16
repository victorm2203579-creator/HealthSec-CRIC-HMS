"""risk_engine/api_urls.py – REST API URL patterns."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CurrentRiskScoreView, RiskScoreViewSet, VulnerabilityViewSet

router = DefaultRouter()
router.register(r'scores', RiskScoreViewSet, basename='riskscore')
router.register(r'vulnerabilities', VulnerabilityViewSet, basename='vulnerability')

urlpatterns = [
    path('', include(router.urls)),
    path('current-score/', CurrentRiskScoreView.as_view(), name='current_risk_score'),
]
