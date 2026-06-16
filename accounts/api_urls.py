"""
accounts/api_urls.py
====================
REST API URL patterns for the accounts app.
Mounted at /api/accounts/ in the root urls.py.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
