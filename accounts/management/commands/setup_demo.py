"""
accounts/management/commands/setup_demo.py
==========================================
One-command demo setup for HealthSec CRIC HMS.

Creates a complete, realistic dataset ready for live demonstration:
  - 6 users (one per role) with predictable credentials
  - 200 patient records across departments
  - 500 access logs with 50 suspicious entries
  - 50 threat events (mixed severities)
  - 30 compliance check results
  - 10 alerts (mixed types/severities)
  - 3 open incidents
  - Runs automated compliance checks
  - Trains the ML anomaly detection model

Usage::

    python manage.py setup_demo
    python manage.py setup_demo --clear    # wipe demo data first
    python manage.py setup_demo --no-ml   # skip ML training (faster)
"""

import random
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


DEMO_USERS = [
    {"username": "admin",      "email": "admin@healthsec.com",      "role": "ADMIN",      "first_name": "Admin",     "last_name": "User",      "password": "Admin@1234"},
    {"username": "analyst",    "email": "analyst@healthsec.com",    "role": "ANALYST",    "first_name": "Alex",      "last_name": "Analyst",   "password": "Analyst@1234"},
    {"username": "compliance", "email": "compliance@healthsec.com", "role": "COMPLIANCE", "first_name": "Carol",     "last_name": "Compliance","password": "Comply@1234"},
    {"username": "viewer",     "email": "viewer@healthsec.com",     "role": "VIEWER",     "first_name": "Victor",    "last_name": "Viewer",    "password": "Viewer@1234"},
    {"username": "dr_smith",   "email": "smith@healthsec.com",      "role": "ANALYST",    "first_name": "Dr. Jane",  "last_name": "Smith",     "password": "Smith@1234"},
    {"username": "nurse_jones","email": "jones@healthsec.com",      "role": "VIEWER",     "first_name": "Nurse Bob", "last_name": "Jones",     "password": "Jones@1234"},
]

DEPARTMENTS = [
    "Cardiology", "Oncology", "Radiology", "Emergency", "Pharmacy",
    "Pathology", "ICU", "Neurology", "Orthopedics", "Pediatrics",
]

RECORD_TYPES = ["MEDICAL_HISTORY", "PRESCRIPTION", "LAB_RESULT", "INSURANCE", "IMAGING", "PERSONAL_INFO"]
SENSITIVITY  = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ACCESS_TYPES = ["VIEW", "EDIT", "DOWNLOAD", "PRINT", "DELETE", "SHARE"]

THREAT_TYPES = [
    "BRUTE_FORCE", "SQL_INJECTION", "UNAUTHORIZED_ACCESS", "INSIDER_THREAT",
    "MALWARE_INDICATOR", "PHISHING_ATTEMPT", "PRIVILEGE_ESCALATION",
    "DATA_EXFILTRATION", "REPEATED_FAILURES", "ANOMALOUS_BEHAVIOR",
]
MITRE_TACTICS = [
    "Initial Access", "Execution", "Persistence", "Privilege Escalation",
    "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
    "Collection", "Exfiltration",
]
ALERT_TYPES = ["SECURITY", "COMPLIANCE", "PERFORMANCE", "AVAILABILITY", "DATA_BREACH",
               "POLICY", "UNAUTH_ACCESS", "PRIV_ESCALATION", "SUSPICIOUS", "AUDIT_ANOMALY"]
ALERT_SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class Command(BaseCommand):
    help = "Populate HealthSec with realistic demo data for presentation."

    def add_arguments(self, parser):
        parser.add_argument("--clear",  action="store_true", help="Delete existing demo data before seeding.")
        parser.add_argument("--no-ml",  action="store_true", help="Skip ML model training step.")
        parser.add_argument("--quiet",  action="store_true", help="Suppress progress output.")

    # ------------------------------------------------------------------ #
    def handle(self, *args, **options):
        self.quiet = options["quiet"]
        self.now   = timezone.now()

        if options["clear"]:
            self._clear_data()

        self._log("=" * 60)
        self._log("  HealthSec CRIC HMS — Demo Setup")
        self._log("=" * 60)

        users      = self._create_users()
        systems    = self._get_or_create_systems(users)
        records    = self._create_patient_records(users)
        self._create_access_logs(users, records)
        self._create_threat_events(users)
        self._create_vulnerabilities()
        self._create_compliance_results(users)
        alerts     = self._create_alerts(systems)
        self._create_incidents(users, alerts)
        self._create_audit_logs(users)

        if not options["no_ml"]:
            self._train_ml_model()

        self._print_summary()

    # ------------------------------------------------------------------ #
    # HELPERS
    # ------------------------------------------------------------------ #
    def _log(self, msg, style=None):
        if not self.quiet:
            if style == "ok":
                self.stdout.write(self.style.SUCCESS(f"  [OK] {msg}"))
            elif style == "warn":
                self.stdout.write(self.style.WARNING(f"  [!!] {msg}"))
            else:
                self.stdout.write(msg)

    def _ago(self, days=0, hours=0, minutes=0):
        return self.now - timedelta(days=days, hours=hours, minutes=minutes)

    # ------------------------------------------------------------------ #
    # CLEAR
    # ------------------------------------------------------------------ #
    def _clear_data(self):
        self._log("Clearing existing demo data...", "warn")
        try:
            from monitoring.models import PatientRecord, RecordAccessLog, SuspiciousActivity, MonitoringEvent
            from risk_engine.models import ThreatEvent, VulnerabilityRecord, ThreatFeed, RiskAssessment
            from compliance.models import ComplianceCheckResult
            from alerts.models import Alert, Incident
            from audit.models import AuditLog
            RecordAccessLog.objects.all().delete()
            SuspiciousActivity.objects.all().delete()
            PatientRecord.objects.all().delete()
            MonitoringEvent.objects.all().delete()
            ThreatEvent.objects.all().delete()
            VulnerabilityRecord.objects.all().delete()
            ThreatFeed.objects.all().delete()
            RiskAssessment.objects.all().delete()
            ComplianceCheckResult.objects.all().delete()
            Incident.objects.all().delete()
            Alert.objects.all().delete()
            AuditLog.objects.all().delete()
            User.objects.filter(username__in=[u["username"] for u in DEMO_USERS]).delete()
        except Exception as e:
            self._log(f"Clear warning: {e}", "warn")

    # ------------------------------------------------------------------ #
    # USERS
    # ------------------------------------------------------------------ #
    def _create_users(self):
        self._log("\n[1/9] Creating demo users...")
        created = []
        for data in DEMO_USERS:
            user, new = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email":        data["email"],
                    "role":         data["role"],
                    "first_name":   data["first_name"],
                    "last_name":    data["last_name"],
                    "must_change_password": False,
                    "is_active":    True,
                },
            )
            if new:
                user.set_password(data["password"])
                user.save()
                self._log(f"Created {user.username} ({user.role})", "ok")
            else:
                self._log(f"Exists  {user.username} ({user.role})")
            created.append(user)
        return created

    # ------------------------------------------------------------------ #
    # HEALTHCARE SYSTEMS
    # ------------------------------------------------------------------ #
    def _get_or_create_systems(self, users):
        from monitoring.models import HealthcareSystem
        admin = next((u for u in users if u.role == "ADMIN"), users[0])
        self._log("\n[2/9] Creating healthcare systems...")
        systems_data = [
            {"name": "EHR Primary",      "system_type": "EHR",      "contains_phi": True,  "status": "ACTIVE"},
            {"name": "Lab Info System",  "system_type": "LIS",      "contains_phi": True,  "status": "ACTIVE"},
            {"name": "PACS Imaging",     "system_type": "PACS",     "contains_phi": True,  "status": "ACTIVE"},
            {"name": "Pharmacy System",  "system_type": "PHARMACY", "contains_phi": True,  "status": "DEGRADED"},
            {"name": "Admin HIS",        "system_type": "HIS",      "contains_phi": False, "status": "ACTIVE"},
        ]
        systems = []
        for d in systems_data:
            s, new = HealthcareSystem.objects.get_or_create(
                name=d["name"],
                defaults={**d, "owner": admin,
                          "ip_address": f"192.168.1.{random.randint(10, 100)}",
                          "hostname": d["name"].lower().replace(" ", "-"),
                          "vendor": random.choice(["Epic", "Cerner", "Allscripts", "athenahealth"]),
                          "version": f"{random.randint(2, 5)}.{random.randint(0, 9)}",
                          "description": f"Healthcare {d['system_type']} system for {d['name']}."},
            )
            systems.append(s)
        self._log(f"Ensured {len(systems)} healthcare systems", "ok")
        return systems

    # ------------------------------------------------------------------ #
    # PATIENT RECORDS
    # ------------------------------------------------------------------ #
    def _create_patient_records(self, users):
        from monitoring.models import PatientRecord
        self._log("\n[3/9] Creating 200 patient records...")
        records = []
        for i in range(200):
            dept = random.choice(DEPARTMENTS)
            creator = random.choice(users)
            r = PatientRecord(
                patient_code=f"PT-{1000 + i:04d}",
                record_type=random.choice(RECORD_TYPES),
                sensitivity_level=random.choices(SENSITIVITY, weights=[30, 35, 25, 10])[0],
                department=dept,
                created_by=creator,
                is_flagged=random.random() < 0.05,
            )
            records.append(r)
        PatientRecord.objects.bulk_create(records, ignore_conflicts=True)
        result = list(PatientRecord.objects.all()[:200])
        self._log(f"Created {len(result)} patient records", "ok")
        return result

    # ------------------------------------------------------------------ #
    # ACCESS LOGS
    # ------------------------------------------------------------------ #
    def _create_access_logs(self, users, records):
        from monitoring.models import RecordAccessLog
        self._log("\n[4/9] Creating 500 access logs (50 suspicious)...")
        logs = []
        ips = [f"10.0.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(20)]
        for i in range(500):
            user   = random.choice(users)
            record = random.choice(records)
            days_ago = random.randint(0, 30)
            is_suspicious = i < 50

            if is_suspicious:
                hour   = random.choice([0, 1, 2, 3, 22, 23])  # after-hours
                reason = random.choice([
                    "After-hours access detected",
                    "Bulk download from multiple departments",
                    "Unusual access volume for user",
                    "Cross-department access on critical record",
                    "Access pattern deviates from baseline",
                ])
            else:
                hour   = random.randint(7, 18)
                reason = ""

            logs.append(RecordAccessLog(
                user=user,
                patient_record=record,
                access_type=random.choice(ACCESS_TYPES),
                ip_address=random.choice(ips),
                device_info=random.choice(["Chrome/Windows", "Firefox/Linux", "Safari/Mac", "Edge/Windows"]),
                access_hour=hour,
                is_suspicious=is_suspicious,
                suspicion_reason=reason,
                session_key=str(uuid.uuid4())[:40],
            ))

        RecordAccessLog.objects.bulk_create(logs)
        self._log("Created 500 access logs (50 flagged suspicious)", "ok")

    # ------------------------------------------------------------------ #
    # THREAT EVENTS
    # ------------------------------------------------------------------ #
    def _create_threat_events(self, users):
        from risk_engine.models import ThreatEvent
        self._log("\n[5/9] Creating 50 threat events...")
        analyst = next((u for u in users if u.role in ("ANALYST", "ADMIN")), users[0])
        events  = []
        sev_weights = {4: 10, 3: 25, 2: 40, 1: 25}  # CRITICAL rare, LOW common
        for i in range(50):
            sev = random.choices(list(sev_weights), weights=list(sev_weights.values()))[0]
            ttype = random.choice(THREAT_TYPES)
            days_ago = random.randint(0, 60)
            events.append(ThreatEvent(
                threat_type=ttype,
                source_ip=f"203.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                target_user=random.choice(users),
                target_resource=random.choice(["/api/patients", "/ehr/records", "/admin/", "/api/export", "/lab/results"]),
                severity=sev,
                risk_score=round(sev * 2.0 + random.uniform(0, 1.5), 2),
                description=f"{ttype.replace('_', ' ').title()} detected from external source. Immediate review required.",
                indicators={"ip": f"203.{random.randint(0,255)}.{random.randint(0,255)}.1", "count": random.randint(1, 100)},
                mitre_tactic=random.choice(MITRE_TACTICS),
                status=random.choices(["OPEN", "INVESTIGATING", "MITIGATED", "FALSE_POSITIVE"], weights=[40, 30, 20, 10])[0],
                assigned_to=analyst if random.random() > 0.5 else None,
            ))
        ThreatEvent.objects.bulk_create(events)
        self._log("Created 50 threat events", "ok")

    # ------------------------------------------------------------------ #
    # VULNERABILITIES
    # ------------------------------------------------------------------ #
    def _create_vulnerabilities(self):
        from risk_engine.models import VulnerabilityRecord
        self._log("\n[5b] Creating 15 vulnerability records...")
        vulns = [
            ("Unpatched OpenSSL CVE-2023-0286",  "CVE-2023-0286", 9.8, "CRITICAL", "OpenSSL 1.1.1"),
            ("Apache Log4Shell Residual Risk",    "CVE-2021-44228",9.0, "CRITICAL", "Log4j 2.x"),
            ("Django Debug Mode Exposed",          "",              7.5, "HIGH",     "Django Framework"),
            ("Weak Password Policy on EHR",        "",              6.8, "HIGH",     "EHR Primary"),
            ("SQL Injection in Patient Search",    "CVE-2023-1234", 8.1, "HIGH",     "Patient Portal"),
            ("Outdated TLS 1.0 on Lab System",    "",              5.9, "MEDIUM",   "LIS TLS Config"),
            ("Missing MFA on Admin Accounts",      "",              7.2, "HIGH",     "IAM Module"),
            ("Unencrypted PHI in Backup",          "",              8.4, "CRITICAL", "Backup Service"),
            ("XSS in Report Generator",            "CVE-2023-5678", 5.4, "MEDIUM",  "Reports Module"),
            ("Default Credentials on PACS",        "",              9.1, "CRITICAL", "PACS Imaging"),
            ("Insecure File Upload Endpoint",      "",              6.1, "MEDIUM",   "Document Upload"),
            ("Expired SSL Certificate",            "",              4.3, "MEDIUM",   "Public API Gateway"),
            ("Missing CSRF Protection",            "",              4.8, "MEDIUM",   "Web Frontend"),
            ("Cleartext Passwords in Config",      "",              8.0, "HIGH",     "Pharmacy System"),
            ("Unnecessary Open Ports",             "",              3.1, "LOW",      "Network Firewall"),
        ]
        records = []
        for title, cve, cvss, sev, component in vulns:
            records.append(VulnerabilityRecord(
                title=title,
                description=f"Security vulnerability in {component}. {title}. Remediation required per HIPAA Security Rule.",
                cve_reference=cve,
                cvss_score=cvss,
                severity=sev,
                affected_component=component,
                discovered_at=timezone.now() - timedelta(days=random.randint(5, 90)),
                patched=random.random() < 0.25,
            ))
        VulnerabilityRecord.objects.bulk_create(records, ignore_conflicts=True)
        self._log("Created 15 vulnerability records", "ok")

    # ------------------------------------------------------------------ #
    # COMPLIANCE
    # ------------------------------------------------------------------ #
    def _create_compliance_results(self, users):
        from compliance.models import ComplianceFramework, ComplianceControl, ComplianceCheckResult, ComplianceReport
        self._log("\n[6/9] Creating compliance data...")
        compliance_user = next((u for u in users if u.role == "COMPLIANCE"), users[0])

        # Ensure frameworks exist
        hipaa, _ = ComplianceFramework.objects.get_or_create(
            short_name="HIPAA",
            defaults={"name": "Health Insurance Portability and Accountability Act",
                      "version": "2013", "issuing_body": "HHS", "applicable_region": "United States", "is_active": True},
        )
        nist, _ = ComplianceFramework.objects.get_or_create(
            short_name="NIST-CSF",
            defaults={"name": "NIST Cybersecurity Framework",
                      "version": "1.1", "issuing_body": "NIST", "applicable_region": "Global", "is_active": True},
        )
        iso, _ = ComplianceFramework.objects.get_or_create(
            short_name="ISO 27001",
            defaults={"name": "ISO/IEC 27001 Information Security",
                      "version": "2022", "issuing_body": "ISO", "applicable_region": "Global", "is_active": True},
        )

        # Ensure controls exist
        controls_data = [
            (hipaa, "HIPAA-164.312(a)(1)", "Access Control",              "ACCESS_CONTROL",     True),
            (hipaa, "HIPAA-164.312(b)",    "Audit Controls",               "AUDIT_LOGGING",      True),
            (hipaa, "HIPAA-164.312(a)(2)", "Automatic Logoff",             "PASSWORD_POLICY",    True),
            (hipaa, "HIPAA-164.312(e)(2)", "Encryption in Transit",        "ENCRYPTION",         True),
            (hipaa, "HIPAA-164.308(a)(6)", "Incident Response Procedure",  "INCIDENT_RESPONSE",  True),
            (nist,  "NIST-ID.AM-1",        "Asset Management",             "RISK_MANAGEMENT",    False),
            (nist,  "NIST-PR.AC-1",        "Identity Management",          "ACCESS_CONTROL",     True),
            (nist,  "NIST-PR.DS-1",        "Data-at-Rest Protection",      "ENCRYPTION",         True),
            (nist,  "NIST-DE.AE-1",        "Network Baseline Established", "NETWORK_SECURITY",   False),
            (nist,  "NIST-RS.CO-1",        "Incident Communication Plan",  "INCIDENT_RESPONSE",  True),
            (iso,   "ISO-A.9.1.1",         "Access Control Policy",        "ACCESS_CONTROL",     True),
            (iso,   "ISO-A.10.1.1",        "Cryptography Policy",          "ENCRYPTION",         True),
            (iso,   "ISO-A.12.4.1",        "Event Logging",                "AUDIT_LOGGING",      True),
            (iso,   "ISO-A.16.1.1",        "Incident Management",          "INCIDENT_RESPONSE",  True),
            (iso,   "ISO-A.18.1.1",        "Legal Requirements",           "RISK_MANAGEMENT",    False),
        ]
        controls = []
        for fw, code, title, cat, automated in controls_data:
            c, _ = ComplianceControl.objects.get_or_create(
                control_code=code,
                defaults={"framework": fw, "title": title, "description": f"Compliance control: {title}",
                          "control_category": cat, "automated_check": automated, "weight": 1.0},
            )
            controls.append(c)

        # Create 30 check results
        status_weights = ["PASS"] * 18 + ["FAIL"] * 6 + ["PARTIAL"] * 4 + ["PENDING"] * 2
        results = []
        for i in range(30):
            ctrl   = controls[i % len(controls)]
            status = random.choice(status_weights)
            score  = {"PASS": random.uniform(85, 100), "PARTIAL": random.uniform(40, 75),
                      "FAIL": random.uniform(0, 35), "PENDING": 0.0, "NOT_APPLICABLE": 100.0}.get(status, 0.0)
            results.append(ComplianceCheckResult(
                control=ctrl,
                checked_by=compliance_user,
                status=status,
                score=round(score, 1),
                notes=f"Automated check result: {status}",
                evidence=f"Log reference: CHK-{1000 + i}",
                remediation_steps="" if status == "PASS" else f"Remediate {ctrl.title} by updating policy and re-testing.",
                due_date=(timezone.now() + timedelta(days=30)).date() if status == "FAIL" else None,
            ))
        ComplianceCheckResult.objects.bulk_create(results)

        # Create a compliance report per framework
        for fw in [hipaa, nist, iso]:
            fw_controls = [c for c in controls if c.framework == fw]
            fw_results  = [r for r in results if r.control.framework == fw]
            passed = sum(1 for r in fw_results if r.status == "PASS")
            failed = sum(1 for r in fw_results if r.status == "FAIL")
            total  = len(fw_results)
            score  = round((passed / max(total, 1)) * 100, 1)
            ComplianceReport.objects.get_or_create(
                framework=fw,
                defaults={"generated_by": compliance_user, "overall_score": score,
                          "compliance_level": "COMPLIANT" if score >= 80 else "PARTIAL",
                          "total_controls": total, "passed_controls": passed, "failed_controls": failed,
                          "summary_json": {"score": score, "passed": passed, "failed": failed}},
            )

        self._log("Created 30 compliance check results + 3 framework reports", "ok")

    # ------------------------------------------------------------------ #
    # ALERTS
    # ------------------------------------------------------------------ #
    def _create_alerts(self, systems):
        from alerts.models import Alert
        self._log("\n[7/9] Creating 10 alerts...")
        alert_data = [
            ("Critical PHI Breach Detected",         "CRITICAL", "DATA_BREACH",    "NEW"),
            ("Unauthorized EHR Access Attempt",      "HIGH",     "UNAUTH_ACCESS",  "IN_PROGRESS"),
            ("Privilege Escalation on Lab System",   "HIGH",     "PRIV_ESCALATION","NEW"),
            ("HIPAA Audit Control Failure",          "HIGH",     "COMPLIANCE",     "ACK"),
            ("Suspicious Bulk Download Activity",    "MEDIUM",   "SUSPICIOUS",     "IN_PROGRESS"),
            ("Pharmacy System Degraded",             "MEDIUM",   "AVAILABILITY",   "ACK"),
            ("After-Hours PHI Access × 12 Events",  "MEDIUM",   "AUDIT_ANOMALY",  "NEW"),
            ("Weak Password Policy Violation",       "LOW",      "POLICY",         "RESOLVED"),
            ("SSL Certificate Expiry in 14 Days",   "LOW",      "PERFORMANCE",    "ACK"),
            ("New Vulnerability CVE-2023-0286",      "CRITICAL", "SECURITY",       "NEW"),
        ]
        created = []
        for i, (title, sev, atype, status) in enumerate(alert_data):
            a, _ = Alert.objects.get_or_create(
                title=title,
                defaults={
                    "description": f"Automated detection: {title}. Review and action required per incident response policy.",
                    "alert_type":  atype,
                    "severity":    sev,
                    "status":      status,
                    "affected_system": systems[i % len(systems)] if systems else None,
                    "is_read":     status != "NEW",
                    "tags":        f"{atype.lower()},{sev.lower()}",
                },
            )
            created.append(a)
        self._log("Created 10 alerts", "ok")
        return created

    # ------------------------------------------------------------------ #
    # INCIDENTS
    # ------------------------------------------------------------------ #
    def _create_incidents(self, users, alerts):
        from alerts.models import Incident
        self._log("\n[8/9] Creating 3 open incidents...")
        analyst = next((u for u in users if u.role in ("ANALYST", "ADMIN")), users[0])
        admin   = next((u for u in users if u.role == "ADMIN"), users[0])
        incidents_data = [
            {
                "title":       "PHI Data Breach — Cardiology Department",
                "description": "Suspected exfiltration of 47 patient records from the Cardiology EHR module. Detected via anomaly detection model.",
                "phase":       "CONTAIN",
                "commander":   analyst,
                "detected_at": timezone.now() - timedelta(hours=6),
                "impact":      "HIGH — PHI of 47 patients potentially exposed. Regulatory notification may be required within 60 days.",
            },
            {
                "title":       "Insider Threat — Pharmacy Credential Misuse",
                "description": "Staff member accessed 200+ patient records outside normal working hours over 3 days.",
                "phase":       "INVESTIGATE",
                "commander":   admin,
                "detected_at": timezone.now() - timedelta(days=2),
                "impact":      "MEDIUM — Potential HIPAA violation. No evidence of external disclosure yet.",
            },
            {
                "title":       "Ransomware Indicator on Lab Workstation",
                "description": "IsolationForest model flagged suspicious file activity on LIS workstation. SHA256 hash matches known ransomware family.",
                "phase":       "ERADICATE",
                "commander":   analyst,
                "detected_at": timezone.now() - timedelta(days=1),
                "impact":      "CRITICAL — Lab system isolated. Backup restoration in progress.",
            },
        ]
        for i, data in enumerate(incidents_data):
            inc, new = Incident.objects.get_or_create(
                title=data["title"],
                defaults={
                    "description":        data["description"],
                    "phase":              data["phase"],
                    "incident_commander": data["commander"],
                    "detected_at":        data["detected_at"],
                    "impact_assessment":  data["impact"],
                    "created_by":         admin,
                    "timeline":           [{"time": data["detected_at"].isoformat(), "event": "Incident detected by monitoring system"}],
                },
            )
            if new and alerts:
                inc.alerts.add(alerts[i])
        self._log("Created 3 open incidents", "ok")

    # ------------------------------------------------------------------ #
    # AUDIT LOGS
    # ------------------------------------------------------------------ #
    def _create_audit_logs(self, users):
        from audit.utils import log_event
        self._log("\n[8b] Seeding audit log entries...")
        admin = next((u for u in users if u.role == "ADMIN"), users[0])
        actions = [
            ("AUTH",             "USER_LOGIN",           "User admin logged in",               "SUCCESS"),
            ("DATA_ACCESS",      "PATIENT_RECORD_VIEW",  "Viewed patient record PT-1001",      "SUCCESS"),
            ("COMPLIANCE",       "COMPLIANCE_CHECK_RUN", "Automated HIPAA check completed",    "SUCCESS"),
            ("ALERT",            "ALERT_ACKNOWLEDGED",   "Alert acknowledged by analyst",      "SUCCESS"),
            ("USER_MANAGEMENT",  "USER_CREATED",         "New user analyst created",           "SUCCESS"),
            ("DATA_MODIFICATION","RECORD_UPDATED",       "Patient record PT-1042 updated",     "SUCCESS"),
            ("AUTH",             "USER_LOGIN",           "Failed login attempt for dr_smith",  "FAILURE"),
            ("SYSTEM",           "ML_MODEL_TRAINED",     "Anomaly detection model trained",    "SUCCESS"),
            ("EXPORT",           "AUDIT_LOG_EXPORTED",   "Audit log exported to CSV",          "SUCCESS"),
            ("COMPLIANCE",       "REPORT_GENERATED",     "HIPAA compliance report generated",  "SUCCESS"),
        ]
        for category, action, desc, status in actions:
            try:
                log_event(
                    user=admin, action_category=category, action=action,
                    description=desc, status=status, ip_address="127.0.0.1",
                )
            except Exception:
                pass
        self._log("Seeded audit log entries", "ok")

    # ------------------------------------------------------------------ #
    # ML MODEL
    # ------------------------------------------------------------------ #
    def _train_ml_model(self):
        self._log("\n[9/9] Training ML anomaly detection model...")
        try:
            from risk_engine.ml_detector import AnomalyDetector
            detector = AnomalyDetector()
            result   = detector.train()
            if result.get("success"):
                self._log(f"ML model trained on {result.get('records_used', '?')} records", "ok")
            else:
                self._log(f"ML training: {result.get('message', 'skipped (not enough data)')}", "warn")
        except Exception as e:
            self._log(f"ML training skipped: {e}", "warn")

    # ------------------------------------------------------------------ #
    # SUMMARY
    # ------------------------------------------------------------------ #
    def _print_summary(self):
        self._log("\n" + "=" * 60)
        self._log("  Demo setup complete!")
        self._log("=" * 60)
        self._log("\n  LOGIN CREDENTIALS:")
        self._log("  " + "-" * 55)
        for u in DEMO_USERS:
            self._log(f"  {u['role']:<12}  {u['email']:<30}  {u['password']}")
        self._log("  " + "-" * 55)
        self._log("\n  Primary demo account:")
        self._log("  Email   : admin@healthsec.com")
        self._log("  Password: Admin@1234")
        self._log("\n  Run: python manage.py runserver")
        self._log("  Open:    http://127.0.0.1:8000/")
        self._log("=" * 60)
