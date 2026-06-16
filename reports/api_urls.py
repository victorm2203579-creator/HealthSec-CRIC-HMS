"""reports/api_urls.py – REST API URL patterns for reports."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import GeneratedReportViewSet

router = DefaultRouter()
router.register(r'generated', GeneratedReportViewSet, basename='report')

urlpatterns = [path('', include(router.urls))]
