# HealthSec CRIC HMS

**Cyber Risk Intelligence and Compliance Healthcare Information Monitoring System**

A final-year university project implementing a full-stack healthcare cybersecurity platform. HealthSec monitors healthcare information systems for threats, enforces HIPAA/NIST/ISO 27001 compliance, detects anomalous access behaviour with machine learning, and provides real-time incident response tooling — all within a HIPAA-aware architecture that keeps Protected Health Information (PHI) out of logs, analytics, and exports.

Built with Django 4.2, Bootstrap 5, Chart.js, Django Channels (WebSockets), and scikit-learn (Isolation Forest). Every access event, policy decision, and system change is recorded in an immutable, checksum-verified audit log.

---

## Features

### 🔐 Authentication & Access Control
- Custom User model with four roles: **VIEWER**, **ANALYST**, **COMPLIANCE**, **ADMIN**
- TOTP-based Two-Factor Authentication (Google Authenticator, Authy, etc.)
- Backup recovery codes for 2FA account recovery
- Rate-limited login (10 attempts / minute per IP)
- Session timeout (30 minutes), HTTPONLY cookies, CSRF protection
- GeoIP location tracking on every login with suspicious-location detection
- Login history with device info and risk scoring

### 🏥 Healthcare System Monitoring
- Register and monitor EHR, LIS, PACS, HIS, and Pharmacy systems
- Track monitoring events by severity: INFO → LOW → MEDIUM → HIGH → CRITICAL
- Patient record registry with sensitivity classification (LOW → CRITICAL)
- Record access logging — every VIEW, EDIT, DOWNLOAD, PRINT, DELETE, SHARE
- Suspicious activity detection: after-hours access, bulk downloads, cross-department access
- User activity heatmap (7 days × 24 hours)

### 🤖 ML Anomaly Detection
- **Isolation Forest** model trained on access log feature vectors
- 11 behavioural features: access hour, day-of-week, is-weekend, volume, cross-department flag, sensitivity level, access type, and user baseline
- Automatic suspicious-activity flagging on prediction outliers
- Audit-safe: no PHI in model artifacts or predictions
- Retrainable on demand via Settings page or management command

### ⚠️ Cyber Risk Engine
- Threat event tracking with MITRE ATT&CK tactic tagging
- CVE-referenced vulnerability records with CVSS scoring
- Threat intelligence feed (IOC types: IP, domain, hash, pattern, signature)
- Risk assessment history with trend charts
- Computed risk score (0–10) aggregated from threat likelihood, impact, vulnerability index, and control effectiveness

### ✅ Compliance Management
- **Frameworks**: HIPAA, NIST CSF 1.1, ISO/IEC 27001:2022 (extensible)
- Automated and manual compliance controls per framework
- Control assessment results: PASS, FAIL, PARTIAL, PENDING, NOT_APPLICABLE
- Compliance score dashboard with framework-by-framework breakdown
- Remediation tracking with due dates
- PDF compliance report generation (ReportLab)

### 🔔 Alerts & Incident Response
- Alert lifecycle: NEW → ACK → IN_PROGRESS → RESOLVED → CLOSED
- Ten alert types covering security, compliance, performance, data breach, and more
- Real-time push notifications via Django Channels WebSockets
- Incident management (PICERL phases: Prep → Detect → Contain → Eradicate → Recover → Post)
- Incident timeline, root cause, lessons learned, and remediation steps

### 📋 Immutable Audit Log
- Every significant action logged with SHA-256 checksum for tamper detection
- Automatic middleware logging of all write HTTP methods (POST/PUT/PATCH/DELETE)
- Manual `log_event()` helper used throughout the codebase
- Integrity check tool compares stored checksums
- Export to CSV, Excel (openpyxl), and PDF (ReportLab)
- Role-gated viewer: ADMIN and COMPLIANCE only

### 📊 Dashboard & Reports
- Live KPI cards: threats today, critical alerts, compliance score, active users, open incidents, vulnerabilities
- Threat timeline chart (30 days)
- Compliance breakdown bar chart
- Risk heatmap (7 × 24)
- Severity distribution donut chart
- PDF report generation for risk and compliance summaries
- Dashboard statistics cached for 60 seconds for performance

### ⚙️ System Settings (ADMIN)
- Session timeout display
- Email configuration status and test button
- Database statistics (users, logs, threats, patients)
- One-click compliance check trigger
- One-click ML model retraining
- Demo data reset with confirmation modal

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 · Python 3.11 |
| Database | SQLite (dev) · PostgreSQL (prod) |
| API | Django REST Framework 3.x |
| Real-time | Django Channels · Daphne (ASGI) · Redis |
| ML | scikit-learn (IsolationForest) · NumPy · joblib |
| PDF | ReportLab |
| Excel | openpyxl |
| Auth | pyotp (TOTP) · qrcode |
| GeoIP | MaxMind GeoLite2 (geoip2) |
| Frontend | Bootstrap 5.3 · Chart.js 4 · Font Awesome 6 |
| Serving | WhiteNoise (static) · Gunicorn/Daphne (WSGI/ASGI) |

---

## Installation

### Prerequisites
- Python 3.11+
- pip
- Git
- (Optional) Redis — required for WebSocket real-time alerts

### Step-by-step

```powershell
# 1. Clone the repository
git clone <repo-url> HEALTH-SEC
cd HEALTH-SEC

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1     # Windows PowerShell
# source venv/bin/activate       # Linux / macOS

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Configure environment variables
Copy-Item .env.example .env
# Open .env and set DJANGO_SECRET_KEY to a strong random string

# 5. Apply database migrations
python manage.py migrate

# 6. Load demo data (creates users, patients, threats, alerts, etc.)
python manage.py setup_demo

# 7. Run the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser.

---

## Running the Project

### Development (HTTP only)
```powershell
python manage.py runserver
```

### With WebSocket support (real-time alerts)
```powershell
# Terminal 1 — Django dev server
python manage.py runserver

# Terminal 2 — Daphne ASGI server for WebSockets
daphne -b 0.0.0.0 -p 8001 healthsec.asgi:application
# Then browse to http://localhost:8001/
```

### Production (Linux)
```bash
# Collect static files
python manage.py collectstatic --no-input

# Start Daphne (handles both HTTP and WebSockets)
daphne -b 0.0.0.0 -p 8000 healthsec.asgi:application
```

---

## Default Login Credentials

> Created automatically by `python manage.py setup_demo`

| Role | Email | Password |
|------|-------|----------|
| **ADMIN** | admin@healthsec.com | `Admin@1234` |
| ANALYST | analyst@healthsec.com | `Analyst@1234` |
| COMPLIANCE | compliance@healthsec.com | `Comply@1234` |
| VIEWER | viewer@healthsec.com | `Viewer@1234` |
| ANALYST (Dr Smith) | smith@healthsec.com | `Smith@1234` |
| VIEWER (Nurse Jones) | jones@healthsec.com | `Jones@1234` |

---

## Demo Dataset

`setup_demo` seeds the following realistic data:

| Entity | Count |
|--------|-------|
| Users | 6 (one per role) |
| Healthcare Systems | 5 (EHR, LIS, PACS, Pharmacy, HIS) |
| Patient Records | 200 |
| Access Logs | 500 (50 flagged suspicious) |
| Threat Events | 50 (mixed CRITICAL → LOW) |
| Vulnerabilities | 15 (with CVE references) |
| Compliance Results | 30 (HIPAA · NIST · ISO 27001) |
| Alerts | 10 (mixed types and severities) |
| Incidents | 3 (open, active) |
| Audit Log Entries | Auto-generated by all actions |

---

## Project Structure

```
HEALTH-SEC/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
│
├── healthsec/              ← Django project config
│   ├── settings.py         ← All settings (loads .env)
│   ├── urls.py             ← Root URL dispatcher
│   ├── asgi.py             ← ASGI + Channels routing
│   └── routing.py          ← WebSocket URL patterns
│
├── accounts/               ← Auth, roles, 2FA, GeoIP
│   ├── models.py           ← User, UserProfile, LoginHistory, TwoFactorAuth
│   ├── views.py            ← login, logout, profile, 2FA flows
│   ├── geoip_service.py    ← MaxMind GeoIP2 lookup + suspicious detection
│   ├── totp_service.py     ← TOTP/backup-code generation and verification
│   └── management/commands/setup_demo.py  ← One-command demo data loader
│
├── monitoring/             ← Healthcare system & record monitoring
│   ├── models.py           ← HealthcareSystem, MonitoringEvent, PatientRecord,
│   │                          RecordAccessLog, SuspiciousActivity, DataAsset
│   └── engine.py           ← MonitoringEngine — rules-based detection
│
├── risk_engine/            ← Cyber risk scoring + ML
│   ├── models.py           ← ThreatEvent, VulnerabilityRecord, ThreatFeed, RiskAssessment
│   ├── ml_detector.py      ← IsolationForest anomaly detector
│   ├── services.py         ← RiskScoringService
│   └── simulator.py        ← Threat simulation for demo data
│
├── compliance/             ← Regulatory framework management
│   ├── models.py           ← ComplianceFramework, ComplianceControl,
│   │                          ComplianceCheckResult, ComplianceReport
│   └── engine.py           ← Automated compliance check runners
│
├── alerts/                 ← Alert generation & incident response
│   ├── models.py           ← Alert, Incident, AlertRule
│   ├── consumers.py        ← WebSocket consumer for real-time push
│   └── context_processors.py ← Injects unread_alerts_count into all templates
│
├── audit/                  ← Immutable audit logging
│   ├── models.py           ← AuditLog (append-only, checksummed)
│   ├── middleware.py        ← AuditLogMiddleware (auto-logs write requests)
│   └── utils.py            ← log_event() helper
│
├── dashboard/              ← Main KPI dashboard
│   ├── views.py            ← MainDashboardView, settings_view, API views
│   └── static/dashboard/   ← dashboard.css, dashboard.js
│
├── reports/                ← PDF + data export
│   └── services.py         ← PDFReportService (ReportLab)
│
├── core/                   ← Shared services
│   └── export_service.py   ← CSV / Excel / PDF export
│
├── templates/              ← Project-level templates
│   ├── base.html           ← Master layout (sidebar, navbar, dark theme)
│   ├── 404.html            ← Custom 404 page
│   └── 500.html            ← Custom 500 page
│
└── static/
    └── js/
        ├── alerts.js       ← WebSocket alert notification manager
        └── hs-loading.js   ← Skeleton loaders & chart fade-in helpers
```

---

## Screenshots

> *(Add screenshots here after running the demo)*

| Page | Description |
|------|-------------|
| `screenshots/dashboard.png` | Main KPI dashboard with live charts |
| `screenshots/monitoring.png` | Patient record access logs |
| `screenshots/risk.png` | Risk engine — threat events |
| `screenshots/compliance.png` | HIPAA/NIST compliance dashboard |
| `screenshots/alerts.png` | Alert list with severity badges |
| `screenshots/audit.png` | Immutable audit log viewer |
| `screenshots/2fa-setup.png` | TOTP two-factor authentication setup |

---

## Security Notes

- Change `DJANGO_SECRET_KEY` before any deployment
- Set `DJANGO_DEBUG=False` in production
- Use PostgreSQL in production (SQLite not suitable for concurrent users)
- Run `python manage.py check --deploy` to verify production readiness
- WebSockets require WSS (TLS) in production
- GeoIP requires the free MaxMind GeoLite2 database (`media/GeoLite2-City.mmdb`)

---

## HIPAA Compliance Design

- No PHI in audit logs, ML model artifacts, or WebSocket payloads
- Opaque internal IDs used throughout — patient codes only, no names
- Role-based minimum-necessary access enforced on every view
- All read/write/export operations produce immutable audit records
- Session timeout, HTTPONLY cookies, and rate-limited login
- Audit log integrity verification with SHA-256 checksums

---

*HealthSec CRIC HMS — Final Year Computer Science Project*
