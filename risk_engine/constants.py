"""
risk_engine/constants.py
========================
Static reference tables for the cyber risk intelligence engine.

MITRE ATT&CK® for Enterprise tactic and technique references used when
classifying ThreatEvent records.  Values are string labels that can be
stored directly in the ThreatEvent.mitre_tactic field and displayed in
templates without any lookup.

Reference: https://attack.mitre.org/tactics/enterprise/
(Knowledge base version 14, 2024)
"""

# ---------------------------------------------------------------------------
# MITRE ATT&CK Tactics (TA-xxxx)
# ---------------------------------------------------------------------------

MITRE_TACTICS = {
    'TA0001': 'Initial Access',
    'TA0002': 'Execution',
    'TA0003': 'Persistence',
    'TA0004': 'Privilege Escalation',
    'TA0005': 'Defense Evasion',
    'TA0006': 'Credential Access',
    'TA0007': 'Discovery',
    'TA0008': 'Lateral Movement',
    'TA0009': 'Collection',
    'TA0010': 'Exfiltration',
    'TA0011': 'Command and Control',
    'TA0040': 'Impact',
    'TA0042': 'Resource Development',
    'TA0043': 'Reconnaissance',
}

# ---------------------------------------------------------------------------
# MITRE ATT&CK Techniques mapped to threat types used in ThreatEvent
# ---------------------------------------------------------------------------

THREAT_TYPE_MITRE_MAP = {
    'BRUTE_FORCE':          ('TA0006', 'T1110', 'Brute Force'),
    'SQL_INJECTION':        ('TA0001', 'T1190', 'Exploit Public-Facing Application'),
    'UNAUTHORIZED_ACCESS':  ('TA0001', 'T1078', 'Valid Accounts (Unauthorised)'),
    'INSIDER_THREAT':       ('TA0009', 'T1074', 'Data Staged'),
    'MALWARE_INDICATOR':    ('TA0002', 'T1204', 'User Execution'),
    'PHISHING_ATTEMPT':     ('TA0001', 'T1566', 'Phishing'),
    'PRIVILEGE_ESCALATION': ('TA0004', 'T1068', 'Exploitation for Privilege Escalation'),
    'DATA_EXFILTRATION':    ('TA0010', 'T1041', 'Exfiltration Over C2 Channel'),
    'REPEATED_FAILURES':    ('TA0006', 'T1110.001', 'Password Guessing'),
    'ANOMALOUS_BEHAVIOR':   ('TA0007', 'T1082', 'System Information Discovery'),
}

# ---------------------------------------------------------------------------
# Severity → display colour helper (used in templates without custom filters)
# ---------------------------------------------------------------------------

SEVERITY_BADGE_CLASSES = {
    1: 'badge-low',
    2: 'badge-medium',
    3: 'badge-high',
    4: 'badge-critical',
}

SEVERITY_LABELS = {
    1: 'LOW',
    2: 'MEDIUM',
    3: 'HIGH',
    4: 'CRITICAL',
}

# ---------------------------------------------------------------------------
# Risk score thresholds  (0-100 scale used by RiskIntelligenceEngine)
# ---------------------------------------------------------------------------

RISK_THRESHOLDS = {
    'LOW':      (0, 25),
    'MEDIUM':   (26, 50),
    'HIGH':     (51, 75),
    'CRITICAL': (76, 100),
}

# ---------------------------------------------------------------------------
# Detection weights used by RiskIntelligenceEngine.calculate_risk_score()
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS = {
    1: 0.1,   # LOW
    2: 0.3,   # MEDIUM
    3: 0.6,   # HIGH
    4: 1.0,   # CRITICAL
}

# ---------------------------------------------------------------------------
# Recommended mitigations per threat type (shown in ThreatEvent detail view)
# ---------------------------------------------------------------------------

THREAT_MITIGATIONS = {
    'BRUTE_FORCE': [
        'Enable account lockout after 5 failed attempts.',
        'Implement multi-factor authentication.',
        'Deploy rate-limiting on authentication endpoints.',
    ],
    'SQL_INJECTION': [
        'Audit all database queries for parameterisation.',
        'Deploy a Web Application Firewall (WAF).',
        'Run OWASP ZAP or Burp Suite against affected endpoints.',
    ],
    'UNAUTHORIZED_ACCESS': [
        'Review and tighten role-based access controls.',
        'Rotate credentials for the affected account.',
        'Audit recent session activity for the user.',
    ],
    'INSIDER_THREAT': [
        'Restrict data export and print capabilities.',
        'Review user access scope against least-privilege principle.',
        'Escalate to HR and legal if warranted.',
    ],
    'MALWARE_INDICATOR': [
        'Isolate the affected system from the network.',
        'Run a full antivirus/EDR scan.',
        'Preserve disk image for forensic analysis.',
    ],
    'PHISHING_ATTEMPT': [
        'Quarantine the phishing email across all mailboxes.',
        'Reset credentials for targeted users.',
        'Send awareness notification to all staff.',
    ],
    'PRIVILEGE_ESCALATION': [
        'Immediately revoke elevated privileges.',
        'Audit sudo/admin group membership.',
        'Patch the exploited vulnerability.',
    ],
    'DATA_EXFILTRATION': [
        'Block the egress IP/domain at the firewall.',
        'Engage the incident response team.',
        'Notify the data protection officer.',
    ],
    'REPEATED_FAILURES': [
        'Lock the targeted account temporarily.',
        'Enable CAPTCHA on login pages.',
        'Investigate source IP for further activity.',
    ],
    'ANOMALOUS_BEHAVIOR': [
        'Review the user\'s access logs for the past 7 days.',
        'Require re-authentication.',
        'Consider restricting account pending investigation.',
    ],
}
