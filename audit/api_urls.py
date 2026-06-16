"""audit/api_urls.py – REST API URL patterns for audit logging."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit_log')

urlpatterns = [
    path('', include(router.urls)),
]
