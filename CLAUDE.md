# HealthSec CRIC HMS — Claude Code Session Guide

> **Project**: Cyber Risk Intelligence and Compliance Healthcare Information Monitoring System
> **Stack**: Django 4.2 · Python 3.11 · PostgreSQL (SQLite fallback) · Bootstrap 5 · Chart.js · ReportLab
> **Author**: Final Year University Project
> **Time Zone**: Africa/Lagos (WAT, UTC+1)

---

## Quick Start

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env – at minimum set DJANGO_SECRET_KEY

# 4. Apply database migrations
python manage.py migrate

# 5. Create superuser (Admin role)
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
# Open http://127.0.0.1:8000/
```

---

## Project Directory Map

```
HEALTH-SEC/                         ← repository root / working directory
│
├── manage.py                       ← Django CLI entrypoint
├── requirements.txt                ← pip dependencies
├── .env.example                    ← environment variable template
├── .env                            ← your local secrets (gitignored)
├── CLAUDE.md                       ← this file
│
├── healthsec/                      ← Django project configuration package
│   ├── __init__.py
│   ├── settings.py                 ← all settings (loads .env via python-dotenv)
│   ├── urls.py                     ← root URL dispatcher
│   ├── wsgi.py                     ← WSGI entrypoint (Gunicorn)
│   └── asgi.py                     ← ASGI entrypoint (Uvicorn / Daphne)
│
├── accounts/                       ← User auth, roles, and profile management
│   ├── models.py                   ← User (AbstractUser), UserProfile
│   ├── views.py                    ← login, logout, profile, register, user list
│   ├── forms.py                    ← LoginForm, UserRegistrationForm, UserProfileForm
│   ├── signals.py                  ← auto-create UserProfile on User save
│   ├── urls.py                     ← /accounts/* HTML routes
│   ├── api_urls.py                 ← /api/accounts/* REST routes
│   ├── api_views.py                ← DRF UserViewSet
│   └── admin.py                    ← Django admin with inline profile
│
├── monitoring/                     ← Healthcare information monitoring
│   ├── models.py                   ← HealthcareSystem, MonitoringEvent, DataAsset
│   ├── views.py                    ← system list/detail, event list
│   ├── urls.py + api_urls.py
│   ├── api_views.py
│   └── admin.py
│
├── risk_engine/                    ← Cyber risk intelligence and scoring
│   ├── models.py                   ← RiskScore, Vulnerability, ThreatIntelFeed
│   ├── services.py                 ← RiskScoringService (core scoring algorithm)
│   ├── views.py                    ← risk dashboard, compute score, vuln list
│   ├── urls.py + api_urls.py
│   ├── api_views.py
│   └── admin.py
│
├── compliance/                     ← Regulatory compliance management
│   ├── models.py                   ← ComplianceFramework, Control, ControlAssessment, Evidence
│   ├── views.py                    ← framework list/detail, control detail, summary
│   ├── urls.py + api_urls.py
│   ├── api_views.py
│   └── admin.py
│
├── alerts/                         ← Alert generation and incident response
│   ├── models.py                   ← Alert, Incident
│   ├── views.py                    ← alert list/detail, acknowledge, resolve, incidents
│   ├── context_processors.py       ← injects unread_alerts_count into all templates
│   ├── urls.py + api_urls.py
│   ├── api_views.py
│   └── admin.py
│
├── audit/                          ← Immutable audit logging
│   ├── models.py                   ← AuditLog (append-only)
│   ├── middleware.py               ← AuditLogMiddleware (logs every POST/PUT/PATCH/DELETE)
│   ├── utils.py                    ← log_event() helper called throughout the project
│   ├── views.py                    ← audit log viewer (compliance/admin only)
│   ├── urls.py
│   └── admin.py                    ← read-only admin (no add/change permissions)
│
├── dashboard/                      ← Aggregated KPI dashboard
│   ├── views.py                    ← index view (queries all other apps)
│   ├── urls.py
│   └── admin.py                    ← empty (no models)
│
├── reports/                        ← PDF and analytics reports
│   ├── models.py                   ← GeneratedReport (tracks created PDFs)
│   ├── services.py                 ← PDFReportService (ReportLab-based PDF builder)
│   ├── views.py                    ← report list, generate_risk_report, generate_compliance_report
│   ├── urls.py + api_urls.py
│   ├── api_views.py
│   └── admin.py
│
├── templates/
│   └── base.html                   ← master layout (Bootstrap 5, Chart.js, FA 6, dark theme)
│
├── static/                         ← project-level static files (CSS overrides, JS, images)
│   └── .gitkeep
│
├── media/                          ← user-uploaded files (avatars, evidence docs, PDFs)
│   └── .gitkeep
│
└── staticfiles/                    ← collectstatic output (gitignored, created at deploy time)
```

---

## User Roles

| Role | Description | Capabilities |
|------|-------------|--------------|
| `VIEWER` | Read-only | Dashboards, reports |
| `ANALYST` | Security analyst | + Review alerts, monitoring events |
| `COMPLIANCE` | Compliance officer | + Assessments, evidence upload, audit log |
| `ADMIN` | System administrator | Full access including user management |

Role is stored on `accounts.User.role` and checked via helper properties:
- `user.is_admin` → True for ADMIN and superusers
- `user.is_compliance_officer` → True for COMPLIANCE and ADMIN
- `user.is_analyst` → True for ANALYST, COMPLIANCE, ADMIN

---

## Key Design Decisions

### Custom User Model
`accounts.User` extends `AbstractUser`. Always reference it via `settings.AUTH_USER_MODEL` or `get_user_model()` — never import `User` directly from `django.contrib.auth.models`.

### Audit Log
Every significant action must call `audit.utils.log_event(...)`. The `AuditLogMiddleware` automatically logs all write HTTP methods (POST/PUT/PATCH/DELETE) from authenticated users. The `AuditLog` model is append-only (admin has no add/change permissions).

### Risk Scoring Algorithm
Located in `risk_engine/services.py`. The `RiskScoringService.compute()` method:
1. Gathers inputs (event counts, open vulns, PHI assets)
2. Normalises to 0–10 component scores
3. Aggregates into a final 0–10 score
4. Persists a `RiskScore` record
5. Returns the `RiskScore` instance

### PDF Generation
`reports/services.py` uses `reportlab` to build PDFs in memory (BytesIO buffer), then streams them as `HttpResponse` with `content_type='application/pdf'`. No temporary files on disk.

### Database
- **Development**: SQLite (default — set `DB_ENGINE=sqlite` or omit in `.env`)
- **Production**: PostgreSQL (set `DB_ENGINE=postgresql` and all `DB_*` variables)

### Static Files
WhiteNoise serves static files in production via `STATICFILES_STORAGE`. Run `python manage.py collectstatic` before deploying.

---

## URL Namespace Reference

| Namespace | Mount Path | Key URL Names |
|-----------|------------|---------------|
| `accounts` | `/accounts/` | `login`, `logout`, `profile`, `change_password`, `user_list`, `register` |
| `dashboard` | `/dashboard/` | `index` |
| `monitoring` | `/monitoring/` | `system_list`, `system_detail`, `event_list` |
| `risk_engine` | `/risk/` | `risk_dashboard`, `compute_risk_score`, `vulnerability_list`, `threat_intel_list` |
| `compliance` | `/compliance/` | `summary`, `framework_list`, `framework_detail`, `control_detail` |
| `alerts` | `/alerts/` | `alert_list`, `alert_detail`, `acknowledge`, `resolve`, `incident_list`, `incident_detail` |
| `audit` | `/audit/` | `log` |
| `reports` | `/reports/` | `report_list`, `generate_risk`, `generate_compliance` |

REST API routes are mounted at `/api/<namespace>/` using DRF DefaultRouter.

---

## Extending the Project

### Adding a new model
1. Define the model in the appropriate app's `models.py`
2. Register it in `admin.py`
3. Create and run a migration: `python manage.py makemigrations && python manage.py migrate`
4. Add DRF serializer + ViewSet in `api_views.py` and register in `api_urls.py`

### Adding a new template
1. Create `<app>/templates/<app>/<page>.html`
2. Start with `{% extends "base.html" %}` and override `{% block content %}`
3. Set `{% block title %}Page Name{% endblock %}` and `{% block page_title %}Page Name{% endblock %}`

### Adding a compliance framework
Use the Django admin at `/admin/compliance/complianceframework/add/` to create a framework, then add controls via `compliance/control/add/`.

---

## Common Management Commands

```powershell
# Run development server
python manage.py runserver

# Create and apply migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Open Django shell for interactive testing
python manage.py shell

# Collect static files for production
python manage.py collectstatic --no-input

# Create a superuser
python manage.py createsuperuser

# Check for project configuration issues
python manage.py check --deploy
```

---

## Security Notes (Important for Deployment)

1. **Change `DJANGO_SECRET_KEY`** — the default in settings.py is insecure.
2. **Set `DJANGO_DEBUG=False`** in production.
3. **Use PostgreSQL** in production — SQLite is not suitable for concurrent users.
4. **Run `manage.py check --deploy`** — it lists all security misconfigurations.
5. **Session timeout** is 30 minutes (`SESSION_COOKIE_AGE = 1800`).
6. **CSRF** protection is enabled on all POST forms via `{% csrf_token %}`.
7. **PHI data** — the `contains_phi` flag on `HealthcareSystem` and `DataAsset.classification` help identify high-impact systems for risk scoring.

---

*This file is loaded by Claude Code at the start of each session to provide project context.*
