"""
healthsec/urls.py
=================
Root URL configuration for the HealthSec project.

Every app registers its own urls.py; this file simply includes them all
under a logical URL prefix.  The Django admin is also mounted here.

URL namespace summary
---------------------
/admin/          → Django admin site
/accounts/       → accounts app  (login, logout, register, profile)
/dashboard/      → dashboard app (main landing page after login)
/monitoring/     → monitoring app (healthcare info monitoring views + API)
/risk/           → risk_engine app (risk scoring, threat intel)
/compliance/     → compliance app (frameworks, control tracking)
/alerts/         → alerts app (active alerts, incident management)
/audit/          → audit app (immutable audit log viewer)
/reports/        → reports app (PDF generation, analytics)
/api/            → REST API root (DRF browsable API entry)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin interface
    path('admin/', admin.site.urls),

    # --- Project apps ---
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('monitoring/', include('monitoring.urls', namespace='monitoring')),
    path('risk/', include('risk_engine.urls', namespace='risk_engine')),
    path('compliance/', include('compliance.urls', namespace='compliance')),
    path('alerts/', include('alerts.urls', namespace='alerts')),
    path('audit/', include('audit.urls', namespace='audit')),
    path('reports/', include('reports.urls', namespace='reports')),

    # --- REST Framework API routes ---
    # Each app also exposes /api/<app>/ endpoints via the same include files
    path('api/accounts/', include('accounts.api_urls')),
    path('api/dashboard/', include('dashboard.api_urls')),
    path('api/monitoring/', include('monitoring.api_urls')),
    path('api/risk/', include('risk_engine.api_urls')),
    path('api/compliance/', include('compliance.api_urls')),
    path('api/alerts/', include('alerts.api_urls')),
    path('api/reports/', include('reports.api_urls')),

    # DRF browsable API auth (login/logout in the browser API explorer)
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# Redirect bare "/" to the dashboard
from django.views.generic import RedirectView
urlpatterns += [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
]

# Serve media files during development only
# In production, media is served by nginx / a CDN
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
