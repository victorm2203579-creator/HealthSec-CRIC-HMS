"""compliance/api_urls.py – REST API URL patterns for compliance."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ComplianceFrameworkViewSet, ControlViewSet, ControlAssessmentViewSet

router = DefaultRouter()
router.register(r'frameworks', ComplianceFrameworkViewSet, basename='framework')
router.register(r'controls', ControlViewSet, basename='control')
router.register(r'assessments', ControlAssessmentViewSet, basename='assessment')

urlpatterns = [path('', include(router.urls))]
