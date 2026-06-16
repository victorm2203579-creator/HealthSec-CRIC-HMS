"""
Generate synthetic healthcare data for HealthSec demo.
Creates HIPAA-safe synthetic patient records and access logs with realistic patterns.

Run: python tools/generate_demo_data.py
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

User = get_user_model()

print(">> Generating synthetic healthcare data...")
print("   All data is synthetic and HIPAA-safe (no real PHI)\n")

from monitoring.models import HealthcareSystem, MonitoringEvent, DataAsset, PatientRecord, RecordAccessLog

# Get or create healthcare system
system, created = HealthcareSystem.objects.get_or_create(
    name='Central Hospital Network',
    defaults={
        'description': 'Primary healthcare system for demo',
        'contains_phi': True,
        'system_type': 'HIS',
    }
)
if created:
    print(f"[OK] Created healthcare system: {system.name}")
else:
    print(f"[INFO] Using existing system: {system.name}")

# Create data assets
classifications = [
    ('PHI', 150, 'Patient Electronic Health Records'),
    ('PHI', 120, 'Laboratory Results Database'),
    ('PII', 100, 'Medical Imaging Repository'),
    ('CONFIDENTIAL', 80, 'Prescription Management System'),
]

asset_count = 0
print("\n>> Creating data assets...")
for classification, count, name_prefix in classifications:
    for i in range(count):
        asset, created = DataAsset.objects.get_or_create(
            system=system,
            name=f"{name_prefix} [{i+1:04d}]",
            defaults={
                'classification': classification,
                'record_count': random.randint(100, 5000),
                'encrypted_at_rest': True,
                'encrypted_in_transit': True,
            }
        )
        if created:
            asset_count += 1

print(f"[OK] Created {asset_count} data assets")

# Get or create demo users
users = list(User.objects.filter(is_active=True))
if len(users) < 4:
    print("\n>> Creating demo users...")
    demo_roles = ['VIEWER', 'ANALYST', 'COMPLIANCE', 'ADMIN']
    for role in demo_roles:
        user, created = User.objects.get_or_create(
            username=f'demo_{role.lower()}',
            defaults={
                'email': f'demo_{role.lower()}@healthsec.local',
                'first_name': role.title(),
                'role': role,
                'is_active': True,
            }
        )
        if user not in users:
            users.append(user)
    print(f"[OK] Created {len([u for u in users if u.username.startswith('demo_')])} demo users")

# Generate monitoring events
event_count = 0
now = timezone.now()
all_assets = list(DataAsset.objects.all())

print("\n>> Generating 300 monitoring events...")
for i in range(300):
    days_ago = random.randint(0, 7)
    occurred_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))

    is_suspicious = random.random() < 0.1  # 10% suspicious
    severity = MonitoringEvent.Severity.CRITICAL if is_suspicious else MonitoringEvent.Severity.INFO
    event_type = random.choice(['SECURITY', 'DATA_ACCESS', 'COMPLIANCE'])

    event = MonitoringEvent.objects.create(
        system=system,
        event_type=event_type,
        severity=severity,
        title=f"Event #{i+1}: {'Suspicious' if is_suspicious else 'Normal'} Activity",
        description=f"Monitoring event - {'Flagged for review' if is_suspicious else 'Routine'}",
        occurred_at=occurred_at,
        raw_data={'severity': severity, 'type': event_type},
    )
    event_count += 1
    if (i + 1) % 100 == 0:
        print(f"  [OK] {i + 1} events generated")

print(f"[OK] Total monitoring events: {event_count}")

# Generate patient records and access logs
print("\n>> Generating patient records and access logs...")
patient_count = 0
for i in range(100):
    patient = PatientRecord.objects.create(
        patient_code=f"PAT-{i+1:06d}",
        record_type=random.choice(PatientRecord.RecordType.values),
        sensitivity_level=random.choice(PatientRecord.SensitivityLevel.values),
        department=random.choice(['Cardiology', 'Oncology', 'ICU', 'ER', 'Pediatrics']),
        created_by=random.choice(users),
    )
    patient_count += 1

print(f"[OK] Created {patient_count} patient records")

# Generate access logs
log_count = 0
patients = list(PatientRecord.objects.all())
for i in range(500):
    is_suspicious = random.random() < 0.05  # 5% suspicious
    hour = random.choice([2, 3, 22, 23]) if is_suspicious else random.randint(8, 17)
    access_type = random.choice(RecordAccessLog.AccessType.values)

    log = RecordAccessLog.objects.create(
        user=random.choice(users),
        patient_record=random.choice(patients),
        access_type=access_type,
        ip_address=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
        device_info=random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
        access_hour=hour,
        is_suspicious=is_suspicious,
        suspicion_reason='After-hours access' if is_suspicious else None,
    )
    log_count += 1
    if (i + 1) % 200 == 0:
        print(f"  [OK] {i + 1} access logs generated")

print(f"[OK] Total access logs: {log_count}")

print("\n=== Healthcare Data Summary ===")
print(f"  - Healthcare Systems: {HealthcareSystem.objects.count()}")
print(f"  - Data Assets: {DataAsset.objects.count()}")
print(f"  - Active Users: {User.objects.filter(is_active=True).count()}")
print(f"  - Monitoring Events: {MonitoringEvent.objects.count()}")
print(f"  - Patient Records: {PatientRecord.objects.count()}")
print(f"  - Access Logs: {RecordAccessLog.objects.count()}")
print(f"\n[DONE] Synthetic healthcare data generated successfully!")
print("   All data is HIPAA-safe and suitable for testing/demos.")
