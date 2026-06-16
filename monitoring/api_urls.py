"""monitoring/api_urls.py – REST API URL patterns for monitoring."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import HealthcareSystemViewSet, MonitoringEventViewSet

router = DefaultRouter()
router.register(r'systems', HealthcareSystemViewSet, basename='system')
router.register(r'events', MonitoringEventViewSet, basename='event')

urlpatterns = [path('', include(router.urls))]
