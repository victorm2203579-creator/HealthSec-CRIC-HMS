"""
Load REAL labeled intrusion-detection data from the NSL-KDD dataset into
HealthSec's ThreatEvent model.

NSL-KDD (Tavallaee, Bagheri, Lu & Ghorbani, 2009) is a refined, de-duplicated
version of the DARPA/KDD Cup 1999 intrusion detection benchmark. It is one of
the most widely cited datasets in IDS/IPS research literature, alongside
CICIDS2017 and UNSW-NB15. Source mirror used here:
https://raw.githubusercontent.com/jmnwong/NSL-KDD-Dataset/master/KDDTrain%2B.txt

Each row is a real, labeled network connection record with 41 standard
KDD features (protocol, service, byte counts, error rates, etc.) and an
attack-type label. This script maps each *attack* row (excluding 'normal'
traffic) into a HealthSec ThreatEvent, preserving the original label and
feature values as indicators for traceability back to the source dataset.

The dataset has no raw timestamps or IP addresses (they were stripped for
anonymization when the benchmark was built); detected_at is therefore
populated with a synthetic timestamp spread across the last 30 days, and
this is explicitly flagged in the stored indicators so nobody mistakes it
for real packet-capture timing.

Run: python tools/load_nslkdd_csv.py [--limit-per-category N]
"""

import argparse
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsec.settings')
import django
django.setup()

from datetime import timedelta
from django.utils import timezone

from risk_engine.models import ThreatEvent

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'datasets', 'KDDTrain+.txt',
)

# The 41 standard NSL-KDD feature names, in column order, followed by
# label (col 42) and difficulty (col 43).
FEATURE_NAMES = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root',
    'num_file_creations', 'num_shells', 'num_access_files', 'num_outbound_cmds',
    'is_host_login', 'is_guest_login', 'count', 'srv_count', 'serror_rate',
    'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate', 'same_srv_rate',
    'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate',
    'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate',
    'dst_host_serror_rate', 'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
    'dst_host_srv_rerror_rate',
]

# Official NSL-KDD attack taxonomy (4 categories used in the original paper).
ATTACK_CATEGORY = {
    # DoS
    'back': 'DoS', 'land': 'DoS', 'neptune': 'DoS', 'pod': 'DoS',
    'smurf': 'DoS', 'teardrop': 'DoS', 'apache2': 'DoS', 'udpstorm': 'DoS',
    'processtable': 'DoS', 'worm': 'DoS', 'mailbomb': 'DoS',
    # Probe (reconnaissance / scanning)
    'ipsweep': 'Probe', 'mscan': 'Probe', 'nmap': 'Probe',
    'portsweep': 'Probe', 'saint': 'Probe', 'satan': 'Probe',
    # R2L (Remote-to-Local: gaining unauthorized local access remotely)
    'ftp_write': 'R2L', 'guess_passwd': 'R2L', 'imap': 'R2L',
    'multihop': 'R2L', 'named': 'R2L', 'phf': 'R2L', 'sendmail': 'R2L',
    'snmpgetattack': 'R2L', 'snmpguess': 'R2L', 'spy': 'R2L',
    'warezclient': 'R2L', 'warezmaster': 'R2L', 'xlock': 'R2L',
    'xsnoop': 'R2L', 'httptunnel': 'R2L',
    # U2R (User-to-Root: privilege escalation)
    'buffer_overflow': 'U2R', 'loadmodule': 'U2R', 'perl': 'U2R',
    'ps': 'U2R', 'rootkit': 'U2R', 'sqlattack': 'U2R', 'xterm': 'U2R',
}

# Map attack category (+ a few specific labels) onto HealthSec's ThreatType
# and Severity choices, plus a representative MITRE ATT&CK tactic.
CATEGORY_MAPPING = {
    'DoS':   {'threat_type': ThreatEvent.ThreatType.ANOMALOUS_BEHAVIOR,
              'severity': ThreatEvent.Severity.HIGH,
              'mitre_tactic': 'Impact (TA0040)'},
    'Probe': {'threat_type': ThreatEvent.ThreatType.UNAUTHORIZED_ACCESS,
              'severity': ThreatEvent.Severity.MEDIUM,
              'mitre_tactic': 'Reconnaissance (TA0043)'},
    'R2L':   {'threat_type': ThreatEvent.ThreatType.UNAUTHORIZED_ACCESS,
              'severity': ThreatEvent.Severity.HIGH,
              'mitre_tactic': 'Initial Access (TA0001)'},
    'U2R':   {'threat_type': ThreatEvent.ThreatType.PRIVILEGE_ESCALATION,
              'severity': ThreatEvent.Severity.CRITICAL,
              'mitre_tactic': 'Privilege Escalation (TA0004)'},
}

# Label-specific overrides where a more precise ThreatType exists.
LABEL_OVERRIDES = {
    'guess_passwd': ThreatEvent.ThreatType.BRUTE_FORCE,
    'sqlattack':    ThreatEvent.ThreatType.SQL_INJECTION,
    'rootkit':      ThreatEvent.ThreatType.MALWARE_INDICATOR,
    'spy':          ThreatEvent.ThreatType.INSIDER_THREAT,
}


def parse_rows(path):
    """Yield (features_dict, label) tuples for every attack row in the file."""
    with open(path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 42:
                continue
            label = row[41].strip()
            if label == 'normal':
                continue
            features = dict(zip(FEATURE_NAMES, row[:41]))
            yield features, label


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit-per-category', type=int, default=40,
                         help='Max ThreatEvents to create per attack category (default 40).')
    args = parser.parse_args()

    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Dataset not found at {DATASET_PATH}")
        print("Download it with:")
        print('  curl --ssl-no-revoke -o datasets/KDDTrain+.txt '
              '"https://raw.githubusercontent.com/jmnwong/NSL-KDD-Dataset/master/KDDTrain%2B.txt"')
        sys.exit(1)

    by_category = {}
    for features, label in parse_rows(DATASET_PATH):
        category = ATTACK_CATEGORY.get(label, 'Other')
        by_category.setdefault(category, []).append((features, label))

    print("Rows available per category in NSL-KDD training set:")
    for cat, rows in by_category.items():
        print(f"  {cat}: {len(rows)} rows")

    now = timezone.now()
    created = 0
    created_ids_with_time = []

    for category, rows in by_category.items():
        mapping = CATEGORY_MAPPING.get(category)
        if not mapping:
            continue
        sample = random.sample(rows, min(args.limit_per_category, len(rows)))

        for features, label in sample:
            threat_type = LABEL_OVERRIDES.get(label, mapping['threat_type'])
            synthetic_detected_at = now - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            event = ThreatEvent.objects.create(
                threat_type=threat_type,
                severity=mapping['severity'],
                target_resource=f"{features['protocol_type']}/{features['service']}",
                description=(
                    f"NSL-KDD labeled connection record: attack type '{label}' "
                    f"({category} category) — protocol={features['protocol_type']}, "
                    f"service={features['service']}, flag={features['flag']}."
                ),
                mitre_tactic=mapping['mitre_tactic'],
                status=ThreatEvent.Status.OPEN,
                indicators={
                    'data_source': 'NSL-KDD (Tavallaee et al., 2009)',
                    'nslkdd_label': label,
                    'attack_category': category,
                    'protocol_type': features['protocol_type'],
                    'service': features['service'],
                    'flag': features['flag'],
                    'src_bytes': features['src_bytes'],
                    'dst_bytes': features['dst_bytes'],
                    'count': features['count'],
                    'srv_count': features['srv_count'],
                    'serror_rate': features['serror_rate'],
                    'same_srv_rate': features['same_srv_rate'],
                    'synthetic_timestamp': True,
                    'note': (
                        'Feature values and attack label are from the real NSL-KDD '
                        'dataset. detected_at is a synthetic timestamp (the dataset '
                        'does not include real capture times); source IP is not '
                        'set because NSL-KDD anonymizes/omits raw IP addresses.'
                    ),
                },
            )
            created_ids_with_time.append((event.pk, synthetic_detected_at))
            created += 1

    # detected_at has auto_now_add=True, so it must be corrected with a
    # queryset update (which bypasses auto_now_add) after creation.
    for pk, ts in created_ids_with_time:
        ThreatEvent.objects.filter(pk=pk).update(detected_at=ts)

    print(f"\n[OK] Created {created} ThreatEvent records from real NSL-KDD data.")
    print(f"     Total ThreatEvent rows in DB now: {ThreatEvent.objects.count()}")
    print("\nCitation for your write-up:")
    print("  Tavallaee, M., Bagheri, E., Lu, W., & Ghorbani, A. (2009).")
    print("  'A Detailed Analysis of the KDD CUP 99 Data Set.' IEEE CISDA.")


if __name__ == '__main__':
    main()
