"""alerts/api_urls.py – REST API URL patterns for alerts."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AlertViewSet, IncidentViewSet

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'incidents', IncidentViewSet, basename='incident')

urlpatterns = [path('', include(router.urls))]
