"""
risk_engine/management/commands/seed_threat_data.py
====================================================
Populates the database with synthetic threat intelligence data for demo
and development purposes.

Creates:
  - 50 random ThreatEvents spread over the last 60 days
  - 10 VulnerabilityRecord entries with realistic CVSS scores
  - 30 ThreatFeed IOC entries (IPs, domains, hashes, patterns, signatures)
  - 5 targeted simulation events (brute force, insider, exfiltration, etc.)

Usage::

    python manage.py seed_threat_data
    python manage.py seed_threat_data --clear    # wipe existing data first
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from risk_engine.models import ThreatFeed, VulnerabilityRecord
from risk_engine.simulator import ThreatSimulator


class Command(BaseCommand):
    help = 'Seeds the database with synthetic threat intelligence data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing ThreatEvent, VulnerabilityRecord, and ThreatFeed data first.',
        )
        parser.add_argument(
            '--events',
            type=int,
            default=50,
            help='Number of random threat events to generate (default: 50).',
        )

    def handle(self, *args, **options):
        if options['clear']:
            from risk_engine.models import ThreatEvent
            deleted_e = ThreatEvent.objects.all().delete()[0]
            deleted_v = VulnerabilityRecord.objects.all().delete()[0]
            deleted_f = ThreatFeed.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(
                f'Cleared {deleted_e} events, {deleted_v} vulns, {deleted_f} feed entries.'
            ))

        sim = ThreatSimulator()

        # 1. Random bulk events
        count = options['events']
        self.stdout.write(f'Generating {count} random threat events…')
        sim.generate_random_threat_events(count=count)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} random events created.'))

        # 2. Specific simulated scenarios
        self.stdout.write('Simulating specific threat scenarios…')
        sim.simulate_brute_force_attack()
        sim.simulate_brute_force_attack()
        sim.simulate_insider_threat()
        sim.simulate_data_exfiltration_attempt()
        sim.simulate_vulnerability_scan()
        self.stdout.write(self.style.SUCCESS('  ✓ 5 scenario events created.'))

        # 3. VulnerabilityRecord entries
        self.stdout.write('Seeding VulnerabilityRecord entries…')
        self._seed_vulns()
        self.stdout.write(self.style.SUCCESS('  ✓ Vulnerability records created.'))

        # 4. ThreatFeed IOC entries
        self.stdout.write('Seeding ThreatFeed IOC entries…')
        self._seed_feed()
        self.stdout.write(self.style.SUCCESS('  ✓ ThreatFeed entries created.'))

        self.stdout.write(self.style.SUCCESS('\nSeed complete. Run the development server to explore.'))

    # ------------------------------------------------------------------
    # Private seeders
    # ------------------------------------------------------------------

    def _seed_vulns(self):
        """Create 10 CVE-style VulnerabilityRecord rows."""
        vulns = [
            {
                'title': 'OpenSSL Heap Buffer Overflow in DTLS',
                'cve_reference': 'CVE-2023-0215',
                'cvss_score': 9.1,
                'severity': 'CRITICAL',
                'affected_component': 'OpenSSL 3.0.x',
                'description': 'A heap-use-after-free vulnerability in the OpenSSL DTLS implementation allows a remote attacker to cause a denial of service.',
            },
            {
                'title': 'Django SQL Injection via JSONField',
                'cve_reference': 'CVE-2023-36053',
                'cvss_score': 7.5,
                'severity': 'HIGH',
                'affected_component': 'Django ≤ 4.2.2',
                'description': 'Potential regular expression denial of service vulnerability in EmailValidator and URLValidator.',
            },
            {
                'title': 'Apache Log4j Remote Code Execution',
                'cve_reference': 'CVE-2021-44228',
                'cvss_score': 10.0,
                'severity': 'CRITICAL',
                'affected_component': 'Log4j 2.0-beta9 to 2.14.1',
                'description': 'JNDI injection vulnerability in Apache Log4j2 allowing unauthenticated remote code execution.',
                'patched': True,
            },
            {
                'title': 'EHR Portal Cross-Site Scripting',
                'cve_reference': '',
                'cvss_score': 6.1,
                'severity': 'MEDIUM',
                'affected_component': 'Internal EHR Portal v2.3',
                'description': 'Reflected XSS in the patient search field allows injection of arbitrary JavaScript.',
            },
            {
                'title': 'Weak TLS Configuration on PACS Server',
                'cve_reference': '',
                'cvss_score': 5.3,
                'severity': 'MEDIUM',
                'affected_component': 'PACS Imaging System — TLS stack',
                'description': 'PACS server accepts TLS 1.0 and weak cipher suites, enabling potential downgrade attacks.',
            },
            {
                'title': 'Microsoft Exchange Server ProxyLogon',
                'cve_reference': 'CVE-2021-26855',
                'cvss_score': 9.8,
                'severity': 'CRITICAL',
                'affected_component': 'Microsoft Exchange Server 2013–2019',
                'description': 'SSRF vulnerability allows unauthenticated attackers to send arbitrary HTTP requests as the Exchange server.',
                'patched': True,
            },
            {
                'title': 'Pharmacy System Default Credentials',
                'cve_reference': '',
                'cvss_score': 8.2,
                'severity': 'HIGH',
                'affected_component': 'Pharmacy Dispensing Module v4.1',
                'description': 'Pharmacy dispensing system ships with unchanged default administrator credentials.',
            },
            {
                'title': 'Unencrypted PHI Backup Files',
                'cve_reference': '',
                'cvss_score': 7.0,
                'severity': 'HIGH',
                'affected_component': 'Backup Storage — NAS Server',
                'description': 'Nightly database backups containing PHI are stored without encryption on a network share.',
            },
            {
                'title': 'Outdated jQuery in Staff Portal',
                'cve_reference': 'CVE-2020-11022',
                'cvss_score': 3.7,
                'severity': 'LOW',
                'affected_component': 'Staff Intranet Portal',
                'description': 'Staff portal uses jQuery 1.9.1 which contains a known XSS vulnerability in the .html() method.',
            },
            {
                'title': 'VPN Gateway Missing Patch MS23-042',
                'cve_reference': 'CVE-2023-20269',
                'cvss_score': 8.8,
                'severity': 'HIGH',
                'affected_component': 'Cisco ASA VPN Gateway',
                'description': 'Unauthenticated remote access VPN brute-force vulnerability in Cisco ASA software.',
            },
        ]

        for i, data in enumerate(vulns):
            days_ago = random.randint(10, 180)
            patched = data.pop('patched', False)
            patched_at = (timezone.now() - timedelta(days=random.randint(1, days_ago - 1))) if patched else None
            VulnerabilityRecord.objects.get_or_create(
                cve_reference=data['cve_reference'],
                title=data['title'],
                defaults={
                    **data,
                    'discovered_at': timezone.now() - timedelta(days=days_ago),
                    'patched': patched,
                    'patched_at': patched_at,
                    'patch_notes': 'Applied vendor patch.' if patched else None,
                },
            )

    def _seed_feed(self):
        """Create 30 ThreatFeed IOC entries across all indicator types."""
        now = timezone.now()

        entries = [
            # IPs
            ('45.33.32.156',      'IP',        'Shodan Scanner',       'Known Mass Scanner',                0.9),
            ('185.220.101.45',    'IP',        'Tor Exit Node',        'Anonymisation Network',             0.85),
            ('91.108.4.0',        'IP',        'APT Infrastructure',   'State-Sponsored C2 Server',         0.95),
            ('198.51.100.42',     'IP',        'Ransomware C2',        'Ransomware Infrastructure',         0.92),
            ('203.0.113.10',      'IP',        'Credential Harvester', 'Phishing Infrastructure',           0.78),
            ('23.95.97.130',      'IP',        'Botnet Node',          'Botnet Command and Control',        0.8),
            ('194.165.16.18',     'IP',        'Threat Intel Feed',    'Known Malicious Host',              0.7),
            ('45.142.212.100',    'IP',        'Brute Force Scanner',  'SSH/RDP Brute Force Source',        0.88),
            # Domains
            ('evil-update.xyz',   'DOMAIN',    'Malware Delivery',     'Fake Software Update Domain',       0.97),
            ('login-verify.co',   'DOMAIN',    'Phishing',             'Credential Harvesting Site',        0.93),
            ('cdn-health.xyz',    'DOMAIN',    'Lookalike Domain',     'Healthcare Brand Lookalike',        0.89),
            ('secure-nhs.net',    'DOMAIN',    'Lookalike Domain',     'NHS Brand Impersonation',           0.91),
            ('update-adobe.cc',   'DOMAIN',    'Malware Delivery',     'Software Update Lookalike',         0.75),
            ('bank-verify.ru',    'DOMAIN',    'Phishing',             'Financial Phishing Domain',         0.85),
            # File Hashes
            ('d41d8cd98f00b204e9800998ecf8427e', 'HASH', 'Malware Sample',   'Known Ransomware Hash (MD5)',    0.99),
            ('aabbcc112233445566778899aabbccdd', 'HASH', 'Trojan Dropper',   'Banking Trojan Hash (MD5)',      0.95),
            ('5891b5b522d5df086d0ff0b110fbd9d2', 'HASH', 'Data Stealer',     'Credential Stealer Hash (MD5)', 0.9),
            ('sha256:abc123def456abc123def456abc123', 'HASH', 'Rootkit',        'Kernel Rootkit Sample (SHA256)',0.87),
            ('sha256:0a1b2c3d4e5f0a1b2c3d4e5f0a1b2c', 'HASH', 'Wiper Malware','Data Wiper Malware (SHA256)',  0.96),
            # Patterns
            ('../../../etc/passwd',        'PATTERN',    'Path Traversal',     'Linux Path Traversal',          0.7),
            ("' OR '1'='1",               'PATTERN',    'SQL Injection',       'Classic SQL Auth Bypass',       0.85),
            ('<script>alert(1)</script>',  'PATTERN',    'XSS',                'Reflected XSS Test Payload',    0.6),
            ('cmd.exe /c whoami',         'PATTERN',    'Command Injection',   'Windows CMD Injection',         0.9),
            ('${jndi:ldap://',            'PATTERN',    'Log4Shell',           'Log4j JNDI Injection Pattern',  0.99),
            ('powershell -enc ',          'PATTERN',    'PowerShell Obfus.',  'Encoded PowerShell Execution',   0.82),
            # Signatures
            ('Mirai-Botnet-SYN-Flood-v2', 'SIGNATURE', 'DDoS',               'Mirai Botnet SYN Flood',         0.88),
            ('Emotet-Email-Payload-2024', 'SIGNATURE', 'Malware',            'Emotet Loader Email Attachment', 0.93),
            ('LockBit-Ransom-Note-v3',    'SIGNATURE', 'Ransomware',         'LockBit 3.0 Ransom Note',        0.98),
            ('CobaltStrike-Beacon-HTTP',  'SIGNATURE', 'C2 Communication',   'Cobalt Strike HTTP Beacon',      0.91),
            ('Brute-Force-SSH-Pattern',   'SIGNATURE', 'Credential Access',  'SSH Brute-Force Attack Pattern', 0.75),
        ]

        for indicator, itype, feed_name, category, confidence in entries:
            days_ago = random.randint(1, 90)
            ThreatFeed.objects.get_or_create(
                threat_indicator=indicator,
                indicator_type=itype,
                defaults={
                    'feed_name': feed_name,
                    'threat_category': category,
                    'confidence_score': confidence,
                    'added_at': now - timedelta(days=days_ago),
                    'is_active': random.random() > 0.1,  # 90% active
                    'source': random.choice([
                        'MISP Community Feed',
                        'AlienVault OTX',
                        'VirusTotal Intelligence',
                        'Shodan Monitor',
                        'Internal SIEM',
                        'NCSC Feed',
                    ]),
                },
            )
