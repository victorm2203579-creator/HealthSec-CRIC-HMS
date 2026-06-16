"""
Load mock threat intelligence data into HealthSec.
Simulates CICIDS2017 attack patterns without requiring external datasets.

Run: python tools/load_threat_data.py
"""

import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsec.settings')
django.setup()

import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from risk_engine.models import ThreatEvent, VulnerabilityRecord
from monitoring.models import HealthcareSystem

User = get_user_model()

print(">> Loading threat intelligence data...")

# Get or create healthcare system
system, _ = HealthcareSystem.objects.get_or_create(
    name='Central Hospital Network',
    defaults={
        'description': 'Primary healthcare system for threat correlation',
        'contains_phi': True,
        'system_type': 'HIS',
    }
)

# Threat patterns with ThreatType (using actual enum values)
threat_patterns = [
    {'threat_type': 'BRUTE_FORCE', 'severity': ThreatEvent.Severity.HIGH, 'count': 8},
    {'threat_type': 'SQL_INJECTION', 'severity': ThreatEvent.Severity.CRITICAL, 'count': 6},
    {'threat_type': 'PRIVILEGE_ESCALATION', 'severity': ThreatEvent.Severity.CRITICAL, 'count': 4},
    {'threat_type': 'DATA_EXFILTRATION', 'severity': ThreatEvent.Severity.CRITICAL, 'count': 5},
    {'threat_type': 'MALWARE_INDICATOR', 'severity': ThreatEvent.Severity.HIGH, 'count': 7},
    {'threat_type': 'UNAUTHORIZED_ACCESS', 'severity': ThreatEvent.Severity.MEDIUM, 'count': 10},
    {'threat_type': 'ANOMALOUS_BEHAVIOR', 'severity': ThreatEvent.Severity.MEDIUM, 'count': 12},
]

# Load threat events
threat_count = 0
now = timezone.now()

for pattern in threat_patterns:
    for i in range(pattern['count']):
        days_ago = random.randint(0, 30)
        detected_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        threat_event = ThreatEvent.objects.create(
            threat_type=pattern['threat_type'],
            severity=pattern['severity'],
            target_resource=f'Resource-{random.randint(1, 50)}',
            description=f'{pattern["threat_type"]} detected on system resource',
            source_ip=f'192.168.{random.randint(1, 254)}.{random.randint(1, 254)}',
            detected_at=detected_at,
            status=random.choice(['OPEN', 'INVESTIGATING', 'MITIGATED']),
        )
        threat_count += 1

print(f"[OK] Loaded {threat_count} threat events")

# CVE patterns for vulnerability records
cve_patterns = [
    {'cve_ref': 'CVE-2024-1234', 'cvss': 9.1, 'product': 'OpenSSL'},
    {'cve_ref': 'CVE-2024-5678', 'cvss': 8.8, 'product': 'Apache HTTPd'},
    {'cve_ref': 'CVE-2024-9012', 'cvss': 7.5, 'product': 'Windows Server'},
    {'cve_ref': 'CVE-2024-3456', 'cvss': 8.9, 'product': 'Linux Kernel'},
    {'cve_ref': 'CVE-2024-7890', 'cvss': 6.8, 'product': 'PostgreSQL'},
    {'cve_ref': 'CVE-2024-2468', 'cvss': 9.3, 'product': 'Django Framework'},
    {'cve_ref': 'CVE-2024-1357', 'cvss': 7.2, 'product': 'Nginx'},
]

# Load vulnerability records
vuln_count = 0
for pattern in cve_patterns:
    for i in range(random.randint(2, 4)):
        discovered_at = now - timedelta(days=random.randint(1, 90))

        severity = (
            VulnerabilityRecord.Severity.CRITICAL if pattern['cvss'] >= 9.0
            else VulnerabilityRecord.Severity.HIGH if pattern['cvss'] >= 7.0
            else VulnerabilityRecord.Severity.MEDIUM
        )

        vulnerability = VulnerabilityRecord.objects.create(
            title=f"{pattern['product']} CVE - Instance {i+1}",
            description=f"Vulnerability in {pattern['product']} - {pattern['cve_ref']}",
            cve_reference=pattern['cve_ref'],
            cvss_score=pattern['cvss'],
            severity=severity,
            affected_component=pattern['product'],
            discovered_at=discovered_at,
            patched=random.choice([True, False]),
        )
        vuln_count += 1

print(f"[OK] Loaded {vuln_count} vulnerability records")

print("\n=== Threat Intelligence Summary ===")
print(f"  - Total Threat Events: {ThreatEvent.objects.count()}")
print(f"  - Total Vulnerabilities: {VulnerabilityRecord.objects.count()}")
print(f"  - Associated System: {system.name}")
print(f"  - Data Span: Last 30 days + historical CVEs")
print("\n[DONE] Threat data loaded successfully!")
