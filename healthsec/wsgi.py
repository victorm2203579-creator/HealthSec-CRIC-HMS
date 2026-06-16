"""
healthsec/wsgi.py
=================
WSGI (Web Server Gateway Interface) config for the HealthSec project.

Used by production WSGI servers such as Gunicorn:
    gunicorn healthsec.wsgi:application --bind 0.0.0.0:8000

Django's `django.core.wsgi` sets up the WSGI callable that forwards
incoming HTTP requests to Django's URL dispatcher.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsec.settings')

application = get_wsgi_application()
