"""dashboard/urls.py – URL patterns for the main dashboard."""

from django.urls import path, include
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.MainDashboardView.as_view(), name='index'),
    path('api/', include('dashboard.api_urls')),
]
