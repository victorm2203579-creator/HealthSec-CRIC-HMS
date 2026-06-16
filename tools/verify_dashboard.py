import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsec.settings')
import django
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS.append('testserver')
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(role='ADMIN').first() or User.objects.filter(is_superuser=True).first()
c = Client()
c.force_login(admin)

r = c.get('/dashboard/')
print("Dashboard status:", r.status_code)
content = r.content.decode()

match = re.search(r'THREATS TODAY.*?kpi-value">(\d+)<', content, re.DOTALL)
if not match:
    match = re.search(r'kpi-value">(\d+)</div>\s*<div class="kpi-label">Threats Today', content, re.DOTALL)
print("Threats Today value found in HTML:", match.group(1) if match else "NOT FOUND (check template structure)")

from risk_engine.models import ThreatEvent
from django.utils import timezone
print("Expected (ThreatEvent today count):", ThreatEvent.objects.filter(detected_at__date=timezone.now().date()).count())

r2 = c.get('/dashboard/api/threat-timeline/')
print("Timeline API status:", r2.status_code, r2.content[:200])
