"""
Load real NSL-KDD dataset into HealthSec.
Takes CSV from Kaggle/UNB and creates ThreatEvent records.
"""
import csv
import os
from django.utils import timezone
from datetime import timedelta
import random

# Map NSL-KDD attack labels to HealthSec attack types
ATTACK_MAPPING = {
    'normal': None,  # Skip normal traffic
    'back': 'DOS',
    'buffer_overflow': 'BUFFER_OVERFLOW',
    'ftp_write': 'PRIVILEGE_ESCALATION',
    'guess_passwd': 'BRUTE_FORCE',
    'imap4': 'BRUTE_FORCE',
    'ipsweep': 'NETWORK_SCAN',
    'land': 'DOS',
    'loadmodule': 'MALWARE',
    'multihop': 'UNAUTHORIZED_ACCESS',
    'nmap': 'NETWORK_SCAN',
    'perl': 'MALWARE',
    'phf': 'PRIVILEGE_ESCALATION',
    'port-sweep': 'NETWORK_SCAN',
    'rootkit': 'MALWARE',
    'satan': 'NETWORK_SCAN',
    'smurf': 'DOS',
    'spy': 'UNAUTHORIZED_ACCESS',
    'teardrop': 'DOS',
    'warezclient': 'DATA_EXFILTRATION',
    'warezmaster': 'DATA_EXFILTRATION',
    'xlock': 'UNAUTHORIZED_ACCESS',
    'xsnoop': 'UNAUTHORIZED_ACCESS',
    'sendmail': 'PRIVILEGE_ESCALATION',
    'named': 'PRIVILEGE_ESCALATION',
    'snmpgetattack': 'PRIVILEGE_ESCALATION',
    'snmpguess': 'BRUTE_FORCE',
    'xterm': 'UNAUTHORIZED_ACCESS',
    'apache2': 'PRIVILEGE_ESCALATION',
    'httptunnel': 'UNAUTHORIZED_ACCESS',
    'mailbomb': 'DOS',
    'udpstorm': 'DOS',
    'saint': 'NETWORK_SCAN',
    'neptune': 'DOS',
    'processtable': 'DOS',
}

def load_nslkdd_real(csv_path, limit=1000):
    """
    Load NSL-KDD CSV into HealthSec ThreatEvent model.

    Args:
        csv_path: Path to KDDTrain+.csv
        limit: Max records to load (default 1000)

    Returns:
        dict with counts
    """
    from risk_engine.models import ThreatEvent

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    created = 0
    skipped = 0
    now = timezone.now()

    print(f"Loading NSL-KDD from: {csv_path}")
    print(f"Limit: {limit} records")
    print()

    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)

        for row_num, row in enumerate(reader):
            if created >= limit:
                print(f"Reached limit of {limit} records")
                break

            try:
                # NSL-KDD format: 43 columns, attack type is column 41 (index 41)
                if len(row) < 42:
                    skipped += 1
                    continue

                # Get attack label from column 41 (index 41) - "normal", "neptune", etc.
                label = row[41].strip().lower() if len(row) > 41 else None
                if not label:
                    skipped += 1
                    continue

                label = label.replace('.', '')
                attack_type = ATTACK_MAPPING.get(label)

                # Skip normal traffic
                if attack_type is None:
                    skipped += 1
                    continue

                # Extract useful fields from NSL-KDD columns
                # Column 1: protocol_type (tcp, udp, icmp)
                # Column 4: src_bytes
                # Column 5: dst_bytes
                try:
                    protocol = row[1].lower() if len(row) > 1 else 'tcp'
                    src_bytes = row[4] if len(row) > 4 else '0'
                    dst_bytes = row[5] if len(row) > 5 else '0'
                except (IndexError, ValueError):
                    protocol = 'tcp'
                    src_bytes = '0'
                    dst_bytes = '0'

                # Random source IP (10.x.x.x range for safety)
                src_ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

                # Random timestamp in past 30 days
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                detected_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

                # Assign severity based on attack type (0-10 scale)
                severity_map = {
                    'DOS': 8,
                    'BRUTE_FORCE': 6,
                    'NETWORK_SCAN': 5,
                    'MALWARE': 10,
                    'DATA_EXFILTRATION': 9,
                    'PRIVILEGE_ESCALATION': 8,
                    'UNAUTHORIZED_ACCESS': 7,
                    'BUFFER_OVERFLOW': 10,
                }
                severity = severity_map.get(attack_type, 5)

                # Create ThreatEvent with NSL-KDD source in description
                threat = ThreatEvent.objects.create(
                    detected_at=detected_at,
                    threat_type=attack_type,
                    source_ip=src_ip,
                    target_resource=f"{protocol.upper()} traffic",
                    description=f"[NSL-KDD] {label} attack from {src_ip} ({src_bytes}b→{dst_bytes}b)",
                    severity=severity,
                    status='OPEN',
                )

                created += 1

                # Progress indicator
                if created % 100 == 0:
                    print(f"  ✓ {created} loaded...")

            except Exception as e:
                skipped += 1
                if row_num < 5:  # Show first few errors only
                    print(f"  Row {row_num}: {str(e)[:60]}")

    print()
    print("=" * 50)
    print(f"[SUCCESS] Created: {created} ThreatEvent records from NSL-KDD")
    print(f"  Skipped: {skipped} (normal traffic or errors)")
    print(f"  Total: {created + skipped}")
    print("=" * 50)

    return {
        'created': created,
        'skipped': skipped,
        'dataset': 'NSL-KDD 2009',
    }

if __name__ == '__main__':
    import sys
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsec.settings')
    django.setup()

    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'tools/KDDTrain+.csv'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    load_nslkdd_real(csv_path, limit=limit)
