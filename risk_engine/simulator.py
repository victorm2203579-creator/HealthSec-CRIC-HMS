"""
risk_engine/simulator.py
========================
ThreatSimulator — generates synthetic threat events for demo and testing.

All methods create ThreatEvent records in the database.  Use the
``seed_threat_data`` management command (or call methods directly in the
Django shell) to populate a fresh environment.

Usage::

    from risk_engine.simulator import ThreatSimulator

    sim = ThreatSimulator()
    sim.generate_random_threat_events(count=50)
"""

import random
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from .constants import THREAT_TYPE_MITRE_MAP
from .models import ThreatEvent

User = get_user_model()

# Sample data pools used when generating synthetic events
_RESOURCES = [
    'EHR Login Portal',
    'Patient Records API',
    'PACS Imaging System',
    'Pharmacy Dispensing Module',
    'Lab Results Database',
    'Admin Dashboard',
    'Staff Email Gateway',
    'VPN Gateway',
    'Billing System',
    'Appointment Scheduler',
]

_SAMPLE_IPS = [
    '45.33.32.156',   # known scanner
    '192.168.0.254',  # internal
    '185.220.101.45', # Tor exit node (simulated)
    '198.51.100.23',  # TEST-NET
    '203.0.113.7',    # TEST-NET
    '10.0.0.99',
    '172.16.0.55',
    '91.108.4.0',
]

_MITRE_LABELS = {k: f'{v[0]} — {v[1]}: {v[2]}' for k, v in THREAT_TYPE_MITRE_MAP.items()}


class ThreatSimulator:
    """
    Factory class that produces realistic-looking synthetic ThreatEvent records.

    Methods are independent and safe to call multiple times.  Each call
    to a simulate_* method creates one or more ThreatEvent database rows.
    """

    # ------------------------------------------------------------------
    # 1. Brute-force simulation
    # ------------------------------------------------------------------

    def simulate_brute_force_attack(self, target_user=None) -> ThreatEvent:
        """
        Simulate a brute-force password attack against a user account.

        Args:
            target_user: A User instance to target, or None to pick randomly.

        Returns:
            ThreatEvent: The created BRUTE_FORCE event.
        """
        if target_user is None:
            target_user = self._random_user()

        attempt_count = random.randint(5, 250)
        source_ip = random.choice(_SAMPLE_IPS)

        return ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.BRUTE_FORCE,
            source_ip=source_ip,
            target_user=target_user,
            target_resource='Authentication Endpoint /accounts/login/',
            severity=ThreatEvent.Severity.HIGH if attempt_count < 50 else ThreatEvent.Severity.CRITICAL,
            risk_score=min(50.0 + attempt_count * 0.2, 100.0),
            description=(
                f"Brute-force attack detected: {attempt_count} failed login attempts "
                f"from {source_ip} targeting account '{target_user.username}'."
            ),
            indicators={
                'source_ip': source_ip,
                'attempt_count': attempt_count,
                'target_username': target_user.username,
                'attack_duration_minutes': random.randint(2, 60),
            },
            mitre_tactic=_MITRE_LABELS['BRUTE_FORCE'],
            status=random.choice([
                ThreatEvent.Status.OPEN,
                ThreatEvent.Status.OPEN,
                ThreatEvent.Status.INVESTIGATING,
            ]),
        )

    # ------------------------------------------------------------------
    # 2. Insider threat simulation
    # ------------------------------------------------------------------

    def simulate_insider_threat(self, user=None) -> ThreatEvent:
        """
        Simulate an insider-threat scenario (data staging, bulk export).

        Args:
            user: A User instance (the suspected insider), or None to pick randomly.

        Returns:
            ThreatEvent: The created INSIDER_THREAT event.
        """
        if user is None:
            user = self._random_user()

        records_accessed = random.randint(50, 500)
        resource = random.choice(_RESOURCES)

        return ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.INSIDER_THREAT,
            target_user=user,
            target_resource=resource,
            severity=ThreatEvent.Severity.HIGH,
            risk_score=random.uniform(60.0, 85.0),
            description=(
                f"Possible insider threat for '{user.username}': "
                f"{records_accessed} records accessed from '{resource}' "
                f"in an unusually short time window."
            ),
            indicators={
                'records_accessed': records_accessed,
                'time_window_minutes': random.randint(5, 30),
                'username': user.username,
                'department': getattr(user, 'department', 'Unknown'),
                'resource': resource,
            },
            mitre_tactic=_MITRE_LABELS['INSIDER_THREAT'],
            status=ThreatEvent.Status.OPEN,
        )

    # ------------------------------------------------------------------
    # 3. Data exfiltration simulation
    # ------------------------------------------------------------------

    def simulate_data_exfiltration_attempt(self) -> ThreatEvent:
        """
        Simulate a data exfiltration attempt (large outbound transfer).

        Returns:
            ThreatEvent: The created DATA_EXFILTRATION event.
        """
        dest_ip = random.choice(_SAMPLE_IPS)
        data_mb = random.randint(50, 2000)
        user = self._random_user()

        return ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.DATA_EXFILTRATION,
            source_ip=dest_ip,
            target_user=user,
            target_resource='Outbound Network — PHI Data Store',
            severity=ThreatEvent.Severity.CRITICAL,
            risk_score=random.uniform(80.0, 100.0),
            description=(
                f"Suspected data exfiltration: {data_mb} MB outbound transfer "
                f"to {dest_ip} from account '{user.username}'. "
                f"Transfer volume far exceeds baseline for this user."
            ),
            indicators={
                'destination_ip': dest_ip,
                'transfer_size_mb': data_mb,
                'protocol': random.choice(['HTTPS', 'FTP', 'SCP', 'SFTP']),
                'username': user.username,
                'port': random.choice([443, 21, 22, 8080]),
            },
            mitre_tactic=_MITRE_LABELS['DATA_EXFILTRATION'],
            status=ThreatEvent.Status.OPEN,
        )

    # ------------------------------------------------------------------
    # 4. Vulnerability scan simulation
    # ------------------------------------------------------------------

    def simulate_vulnerability_scan(self) -> ThreatEvent:
        """
        Simulate an automated vulnerability/port scan against the system.

        Returns:
            ThreatEvent: The created ANOMALOUS_BEHAVIOR event.
        """
        scanner_ip = random.choice(_SAMPLE_IPS)
        ports_scanned = random.randint(100, 65535)
        target = random.choice(_RESOURCES)

        return ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.ANOMALOUS_BEHAVIOR,
            source_ip=scanner_ip,
            target_resource=target,
            severity=ThreatEvent.Severity.MEDIUM,
            risk_score=random.uniform(30.0, 60.0),
            description=(
                f"Automated vulnerability scan detected from {scanner_ip}: "
                f"{ports_scanned} ports probed against '{target}'. "
                f"Possible reconnaissance before an attack."
            ),
            indicators={
                'scanner_ip': scanner_ip,
                'ports_scanned': ports_scanned,
                'scan_type': random.choice(['SYN', 'UDP', 'ACK', 'XMAS', 'NULL']),
                'scan_duration_seconds': random.randint(10, 300),
                'target_resource': target,
            },
            mitre_tactic=_MITRE_LABELS['ANOMALOUS_BEHAVIOR'],
            status=random.choice([ThreatEvent.Status.OPEN, ThreatEvent.Status.INVESTIGATING]),
        )

    # ------------------------------------------------------------------
    # 5. Bulk random event generation
    # ------------------------------------------------------------------

    def generate_random_threat_events(self, count: int = 50) -> list:
        """
        Generate `count` random threat events spread over the last 60 days.

        The distribution is weighted toward more realistic threat mixes:
          40% OPEN, 30% INVESTIGATING, 20% MITIGATED, 10% FALSE_POSITIVE

        Args:
            count: Number of ThreatEvent records to create.

        Returns:
            list[ThreatEvent]: All created events.
        """
        all_types = list(ThreatEvent.ThreatType.values)
        all_severities = [
            ThreatEvent.Severity.LOW,
            ThreatEvent.Severity.LOW,
            ThreatEvent.Severity.MEDIUM,
            ThreatEvent.Severity.MEDIUM,
            ThreatEvent.Severity.MEDIUM,
            ThreatEvent.Severity.HIGH,
            ThreatEvent.Severity.HIGH,
            ThreatEvent.Severity.CRITICAL,
        ]
        status_pool = (
            [ThreatEvent.Status.OPEN] * 4
            + [ThreatEvent.Status.INVESTIGATING] * 3
            + [ThreatEvent.Status.MITIGATED] * 2
            + [ThreatEvent.Status.FALSE_POSITIVE] * 1
        )
        users = list(User.objects.filter(is_active=True))
        created = []

        for _ in range(count):
            ttype = random.choice(all_types)
            severity = random.choice(all_severities)
            days_back = random.randint(0, 60)
            hour = random.randint(0, 23)
            ts = (timezone.now() - timedelta(days=days_back)).replace(
                hour=hour, minute=random.randint(0, 59), second=0, microsecond=0,
            )
            tactic_info = THREAT_TYPE_MITRE_MAP.get(ttype, ('', '', ''))
            mitre = f'{tactic_info[0]} — {tactic_info[1]}: {tactic_info[2]}' if tactic_info[0] else ''
            target_user = random.choice(users) if users and random.random() > 0.3 else None

            evt = ThreatEvent(
                threat_type=ttype,
                source_ip=random.choice(_SAMPLE_IPS) if random.random() > 0.4 else None,
                target_user=target_user,
                target_resource=random.choice(_RESOURCES),
                severity=severity,
                risk_score=round(random.uniform(10.0, 100.0), 1),
                description=self._random_description(ttype, severity),
                indicators={'simulated': True, 'seed_run': True},
                mitre_tactic=mitre,
                status=random.choice(status_pool),
            )
            created.append(evt)

        ThreatEvent.objects.bulk_create(created)

        # Backdate all timestamps via a bulk update
        for evt in ThreatEvent.objects.filter(indicators__simulated=True).order_by('-detected_at')[:count]:
            days_back = random.randint(0, 60)
            hour = random.randint(0, 23)
            backdated = (timezone.now() - timedelta(days=days_back)).replace(
                hour=hour, minute=random.randint(0, 59), second=0, microsecond=0,
            )
            ThreatEvent.objects.filter(pk=evt.pk).update(detected_at=backdated)

        return list(ThreatEvent.objects.filter(indicators__simulated=True)[:count])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _random_user(self):
        """Return a random active user or the first user found."""
        users = list(User.objects.filter(is_active=True))
        return random.choice(users) if users else User.objects.first()

    def _random_description(self, threat_type: str, severity: int) -> str:
        """Generate a plausible description string for the given threat type."""
        templates = {
            'BRUTE_FORCE':          'Automated credential stuffing detected against login endpoint.',
            'SQL_INJECTION':        'SQL injection payload observed in web request parameters.',
            'UNAUTHORIZED_ACCESS':  'Access attempt by account without required permissions.',
            'INSIDER_THREAT':       'Unusual bulk data access pattern from internal user account.',
            'MALWARE_INDICATOR':    'Known malware C2 callback signature detected in network traffic.',
            'PHISHING_ATTEMPT':     'Phishing email with credential-harvesting link delivered to staff.',
            'PRIVILEGE_ESCALATION': 'Exploitation of misconfigured SUID binary detected.',
            'DATA_EXFILTRATION':    'Anomalous outbound data transfer to unrecognised external host.',
            'REPEATED_FAILURES':    'Repeated authentication failures across multiple accounts.',
            'ANOMALOUS_BEHAVIOR':   'Automated port scan detected from external IP range.',
        }
        base = templates.get(threat_type, 'Anomalous activity detected.')
        suffix = {
            ThreatEvent.Severity.CRITICAL: ' Immediate response required.',
            ThreatEvent.Severity.HIGH:     ' Analyst review recommended within 4 hours.',
            ThreatEvent.Severity.MEDIUM:   ' Log for review at next shift briefing.',
            ThreatEvent.Severity.LOW:      ' Monitor for recurrence.',
        }.get(severity, '')
        return base + suffix
