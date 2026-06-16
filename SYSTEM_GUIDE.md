# HealthSec CRIC HMS — Full System Guide

This document explains **every page, field, button, and parameter** in the system
in plain English, so you can operate it confidently and defend it to your supervisor.

It's organized by sidebar section, in the order they appear in the navigation.

---

## 0. The big picture — what is this system actually for?

HealthSec is a **monitoring and compliance dashboard for a hospital's IT security team.**
It does NOT treat patients or store real medical records. It answers four questions for
a hospital's security/compliance officer:

1. **"Is anything suspicious happening to our systems right now?"** → Monitoring
2. **"How risky is our overall security posture today?"** → Risk Engine
3. **"Are we following HIPAA/NDPR/ISO rules?"** → Compliance
4. **"When something bad happens, who's handling it and what did they do?"** → Alerts/Incidents + Audit Log

Everything else (Dashboard, Reports) is a summary/output layer built on top of those four.

The **data flow** is: Monitoring detects events → Risk Engine scores how dangerous they
are → Alerts get raised when something crosses a threshold → Incidents track the human
response → Compliance checks whether your *controls* (policies/configs) are adequate →
Audit Log silently records every action anyone takes → Reports turn all of this into a PDF
you can hand to an auditor or regulator.

---

## 1. Dashboard (`/dashboard/`)

**Purpose**: A single-page summary of the whole system's health — the page you show first
in a demo.

**KPI cards** (top row), each pulled live from the database (cached 60 seconds so the page
loads fast):

| Card | What it counts | Where it comes from |
|---|---|---|
| Total Threats Today | `MonitoringEvent` rows created today, any severity | Monitoring app |
| Critical Alerts Open | `Alert` rows with severity=CRITICAL and status not yet resolved | Alerts app |
| Compliance Score | % of `ComplianceCheckResult` rows with status=PASS | Compliance app |
| Suspicious Activities Today | `RecordAccessLog` rows flagged `is_suspicious=True` | Monitoring app |
| Active Users Today | Distinct users who appear in the Audit Log today | Audit app |
| Open Incidents | `Incident` rows not yet in the CLOSED phase | Alerts app |
| Open Vulnerabilities | `VulnerabilityRecord` rows not yet patched | Risk Engine app |

**Charts** (powered by 4 small REST API endpoints under `dashboard/api_views` so they can
refresh independently via AJAX without reloading the page):
- **Threat Timeline** — daily count of monitoring events for the last 30 days (line chart)
- **Compliance Breakdown** — pass/fail counts per framework (bar chart)
- **Risk Heatmap** — 7×24 grid (day of week × hour) showing when threats cluster; useful
  for spotting "attacks always happen at 2am" patterns
- **Severity Distribution** — donut chart of open alerts by severity

**Recent Activity panel**: last 10 rows from the Audit Log (every important system action,
not just security events) and last 5 high/critical alerts.

**System status row**: whether any `HealthcareSystem` is marked ACTIVE, total system count,
and how many of those systems are flagged `contains_phi=True` (handle Protected Health
Information).

---

## 2. Monitoring

This is the "what's happening right now" layer. Three pages.

### 2a. Healthcare Systems (`/monitoring/`)

A list of the IT systems being watched (e.g. an EHR, a lab system, a pharmacy system).
Each row is one `HealthcareSystem` record.

**Fields you'll see**:
- **Name** — e.g. "Central Hospital Network"
- **System Type** — EHR / LIS (Lab) / PACS (Imaging) / HIS (Hospital Info System) /
  Pharmacy / Other
- **Status** — Active / Degraded / Offline / Under Maintenance
- **Contains PHI** — a yes/no flag. This is the single most important field in the whole
  system: anything marked `contains_phi=True` gets weighted higher in risk scoring,
  because a breach there is a HIPAA violation, not just an IT inconvenience.
- **IP Address / Hostname / Vendor / Version** — basic asset inventory info

Clicking into a system (**System Detail**) shows its last 50 `MonitoringEvent` rows
(security incidents, performance issues, config changes logged against that system) and
its `DataAsset` list (what kind of data it holds — PHI, PII, Confidential, Internal,
Public — and whether that data is encrypted at rest/in transit).

### 2b. Monitoring Events (`/monitoring/events/`)

A flat table of every `MonitoringEvent` ever logged, across all systems, filterable by
severity (Info/Low/Medium/High/Critical).

**Columns**: Severity badge, System name, Event Type (Security / Performance /
Availability / Compliance Violation / Config Change / Data Access Anomaly), Description,
**Timestamp** (this is `occurred_at` — when the event actually happened, not when it was
recorded into the database — that distinction matters because in a real system there's a
detection lag).

This is your raw evidence feed — if your supervisor asks "show me proof something
happened," this page is it.

### 2c. Suspicious Activity (`/monitoring/suspicious/`)

This is a *different* model from Monitoring Events: `SuspiciousActivity`, generated
specifically from patient-record access patterns (`RecordAccessLog`). The distinction
matters for your defense: Monitoring Events = system-level events; Suspicious Activity =
**user behavior** flags, e.g.:

- **After-Hours Access** — someone viewed a record at 2am
- **Bulk Download** — someone pulled an unusually large number of records at once
- **Cross-Department Access** — a Cardiology nurse looking at an Oncology patient's file
- **Privilege Escalation** — someone accessed something above their normal permission level
- **Unauthorized Attempt** — a blocked access attempt
- **Unusual Volume** — abnormal access frequency for that user

Each flagged activity shows: the user, what they accessed, severity, and a **Resolve**
button — an analyst marks it reviewed once they've confirmed it was legitimate (or
escalated it into an Incident if not).

**Why two separate "suspicious" concepts exist**: `MonitoringEvent` severity=HIGH/CRITICAL
is about *system health*; `SuspiciousActivity` is specifically about *who accessed what,
and was that normal for them*. In a real hospital, these come from different detection
logic (network/system monitoring vs. access-pattern analysis), so the system models them
separately even though both can lead to an Alert.

---

## 3. Risk Engine

This is the analytical layer — it takes raw monitoring data and turns it into a single,
defensible risk number.

### 3a. Risk Dashboard (`/risk/`)

**Overall Risk Score** (0–10) — calculated by `RiskIntelligenceEngine.calculate_risk_score()`
from all currently OPEN or INVESTIGATING `ThreatEvent` records. Color-coded: Low (green) →
Medium (blue) → High (orange) → Critical (red).

**KPI row**: Open Threats, Critical Count, Unpatched Vulnerabilities, Last Assessment Date.

**30-Day Threat Trend** chart — daily threat event counts, so you can show your supervisor
"threats are trending down/up over the last month."

**Severity Distribution donut** — Low/Medium/High/Critical split of open threats.

**Recent Threat Events table** — the 10 newest unresolved threats.

There's also a **legacy section** showing `RiskScore` records computed per-`HealthcareSystem`
by an older, simpler scoring service (`RiskScoringService` in `risk_engine/services.py`).
You can trigger a fresh computation per-system with the "Compute Score" button. This
algorithm is intentionally simple and explainable (see box below) — useful to cite in your
defense as "auditable, not a black-box ML score."

> **The legacy scoring formula** (CVSS-inspired, no ML):
> ```
> residual_risk = threat_likelihood × impact_magnitude × (1 − control_effectiveness)
> raw_score     = residual_risk + vulnerability_index
> final_score   = min(raw_score, 10.0)
> ```
> - `threat_likelihood` — driven by how many CRITICAL/HIGH monitoring events that system
>   has had recently
> - `impact_magnitude` — starts at 5/10, +2 if the system contains PHI, +up to 2 more
>   based on how many PHI/PII data assets it holds
> - `vulnerability_index` — the average CVSS score of that system's open vulnerabilities
> - `control_effectiveness` — currently a flat placeholder (5/10 = "50% baseline maturity");
>   in a future version this would pull from the Compliance module's actual control scores

### 3b. Threat Events (`/risk/threats/`)

The detailed, filterable list behind the dashboard's "Recent Threat Events." Each row is
one `ThreatEvent`:

- **Threat Type** — Brute Force, SQL Injection, Unauthorized Access, Insider Threat,
  Malware Indicator, Phishing Attempt, Privilege Escalation, Data Exfiltration, Repeated
  Failures, Anomalous Behavior
- **Severity** — Low / Medium / High / Critical (numeric 1–4 internally, so it can be
  averaged/sorted mathematically, not just sorted alphabetically)
- **Status** — Open → Investigating → Mitigated, or False Positive
- **Source IP**, **Target Resource**, **Detected At**
- **MITRE Tactic** — optional reference to the MITRE ATT&CK framework (a real industry
  taxonomy of attacker techniques) — good to mention to your supervisor as showing
  alignment with industry-standard threat classification

Filters: threat type, severity, status, date range. Analysts (and above) can change a
threat's status inline, and the system auto-assigns it to whoever marks it "Investigating."

**Threat Detail page** — clicking a threat shows its raw `indicators` JSON (technical
evidence captured at detection time), recommended mitigations (pulled from a static lookup
table in `risk_engine/constants.py` keyed by threat type), and lets an analyst reassign or
update status.

### 3c. Vulnerabilities (`/risk/vulnerabilities/`)

CVE-style records (`VulnerabilityRecord`) — these are *known weaknesses*, distinct from
*active threats*. A vulnerability can exist for months unpatched without ever being
exploited; a threat event is something that already happened.

- **CVE Reference** — e.g. CVE-2024-1234 (real-world vulnerability identifiers)
- **CVSS Score** — industry-standard 0–10 severity score
- **Affected Component** — e.g. "OpenSSL", "Django Framework"
- **Patched** (yes/no) — analysts can click "Mark Patched" with optional patch notes, which
  timestamps `patched_at` for compliance evidence ("we fixed this on this date")

Filterable by severity and patch status. The "Unpatched Critical" count on this page is a
good number to highlight to a supervisor — it's the single clearest "are we exposed right
now" metric.

### 3d. Risk Assessment (`/risk/assessment/`)

A *point-in-time snapshot* — different from the live dashboard score. Clicking "Generate
Assessment" runs `RiskIntelligenceEngine.generate_risk_assessment()`, which aggregates
everything (threat counts by severity, top threats, a written recommendation) into one
`RiskAssessment` record with a `next_assessment_due` date. This mirrors how real risk
assessments work in compliance frameworks — periodic, dated, and kept as historical
evidence rather than only showing "right now."

---

## 4. Compliance

This module answers "are we following the rules," separate from "are we under attack."

### 4a. Compliance Dashboard (`/compliance/`)

Shows every active `ComplianceFramework` (e.g. HIPAA, NDPR, ISO 27001) with:
- **Overall Score** — weighted average of all its controls' latest check results
- **Compliance Level** badge — Non-Compliant (<40%) / Partial (40–69%) / Compliant (70–89%)
  / Fully Compliant (≥90%)
- **Pass/Fail/Partial/Pending donut** for that framework

**"Run Automated Check" button** (Compliance Officer/Admin only) — triggers
`ComplianceChecker.run_all_automated_checks()`, which re-evaluates every control flagged
`automated_check=True` (e.g., checking whether encryption is actually enabled on systems,
whether audit logging is active) and writes a fresh `ComplianceCheckResult` for each. It
then snapshots the whole run into a `ComplianceReport`. Controls NOT flagged as automated
need a human to assess them manually (see Remediation below).

### 4b. Controls (`/compliance/controls/`)

The full list of `ComplianceControl` records — each one is a single rule from a framework,
e.g. "HIPAA-164.308(a)(1): Security Management Process." Fields:

- **Control Code** — the formal regulatory citation
- **Category** — Access Control, Audit Logging, Encryption, Incident Response, Risk
  Management, Physical Security, Training, Data Backup, Password Policy, Network Security
- **Weight** (0.0–1.0) — how much this control counts toward the framework's overall score;
  a control critical to patient safety should be weighted higher than a minor
  administrative one
- **Latest Result** — Pass/Fail/Partial/Not Applicable/Pending, with a score 0–100

Filterable by framework, category, and status.

### 4c. Remediation (`/compliance/remediation/`)

Everything currently **failing or partial** — this is your action list. Shows fail/partial/
pending counts at the top. A Compliance Officer can manually override a control's status
here (e.g., "we fixed the encryption gap, mark it Pass now") — this writes a new
`ComplianceCheckResult` with notes explaining why, preserving history rather than editing
the old record (compliance evidence must be append-only/auditable, never silently edited).

### 4d. Compliance Reports (`/compliance/reports/`)

Historical list of every `ComplianceReport` snapshot ever generated, with a score **delta**
column comparing the two most recent reports per framework — so you can show "we improved
from 62% to 78% compliance over the last month" as a defensible trend, not just a single
number.

---

## 5. Alerts & Incidents

This is the human-response layer.

### 5a. Alert Dashboard (`/alerts/`)

KPIs + the 5 most recent open alerts and open incidents.

### 5b. Alerts (`/alerts/...`)

An `Alert` is raised automatically (or, in a future version, by a rule engine —
`AlertRule` model exists for threshold/pattern-based auto-generation) when something
crosses a threshold. Lifecycle:

```
NEW → ACKNOWLEDGED → IN_PROGRESS → RESOLVED | CLOSED | FALSE_POSITIVE
```

Fields: **Alert Type** (Security/Compliance/Performance/Availability/Data Breach
Risk/Policy/Unauthorized Access/Privilege Escalation/Suspicious Activity/Audit Anomaly),
**Severity**, **Status**, which `HealthcareSystem` it affects, which `MonitoringEvent`
triggered it (if any), who it's **Assigned To**.

Actions available on an alert's detail page: **Acknowledge** (I've seen this), **Resolve**
(with a resolution status and notes), **Assign to me**.

### 5c. Incidents (`/alerts/incidents/...`)

An `Incident` is a *formal* response process built from one or more related alerts — used
when something is serious enough to need a coordinated response, not just "ack and move
on." It follows the **NIST Incident Response lifecycle**, which is a real, citable
industry standard — worth mentioning to your supervisor:

```
Preparation → Detection & Analysis → Containment → Eradication → Recovery → Post-Incident Activity → Closed
```

Each incident gets an auto-generated number like `INC-2026-0001` (year + sequence).
Fields: **Incident Commander** (who's leading response), **Impact Assessment**, **Root
Cause**, **Lessons Learned**, **Remediation Steps**, and a JSON **Timeline** that
auto-logs every phase transition and action taken with a timestamp — this timeline is
literally how you'd demonstrate incident response maturity in an audit.

**Create Incident** — pick a title/description, select which open alerts belong to it,
optionally self-assign as commander.

---

## 6. Audit Log (`/audit/`)

**This is the system's memory — every meaningful write action anyone takes gets recorded
here, automatically**, via `AuditLogMiddleware` (catches every POST/PUT/PATCH/DELETE) plus
explicit calls to `log_event()` sprinkled through the views for actions that need richer
description than the middleware alone provides.

Fields per entry:
- **Timestamp**, **User** (who did it — "System" if automated)
- **Action** — a short code like `LOGIN`, `ALERT_ASSIGNED`, `USER_CREATED`
- **Category** — Authentication, Data Access, Data Modification, User Management,
  Compliance, Alert Management, System Events, Data Export, Configuration
- **Target** — which model/record was affected
- **Status** — Success/Failure/Error
- **IP Address**
- **Checksum** — a SHA256 hash of the entry's contents

**Why the checksum matters (this is a strong point for your defense)**: the `AuditLog`
model overrides `.delete()` to always raise `PermissionDenied` — audit logs cannot be
deleted through the application, period, not even by an admin. The checksum lets you prove
an entry hasn't been silently edited after the fact (tamper-evidence). This directly
satisfies HIPAA's audit-control requirement (45 CFR §164.312(b)) — you can cite that
section number directly.

There's also an **Integrity Check** feature (`AuditLogIntegrityCheck` model) — a periodic
job that re-verifies every log's checksum and records whether tampering was detected.

---

## 7. Reports (`/reports/`)

Generates downloadable PDFs via `reports/services.py` (built with ReportLab, entirely
in-memory — no temp files written to disk, which matters for HIPAA since you don't want
PHI-adjacent reports sitting around as orphaned files).

Two report types:
- **Risk Summary Report** — pulls the last 50 `RiskScore` records and renders them as a PDF
- **Compliance Report** — for one specific framework, pulls all its `ControlAssessment`
  records

Every report generation is itself logged to the Audit Log (`REPORT_GENERATED` action) —
so even *who downloaded what report and when* is tracked.

---

## 8. Users / Accounts

### 8a. Roles — the permission model

| Role | Can do |
|---|---|
| **Viewer** | Read-only: dashboards, reports |
| **Analyst** | + review/triage alerts, update threat status, mark vulnerabilities patched |
| **Compliance Officer** | + run compliance checks, override control status, generate compliance reports |
| **Admin** | + create/manage user accounts, full Django admin access |

Checked via three properties on the `User` model: `is_admin`, `is_compliance_officer`,
`is_analyst` (each role inherits the permissions of roles below it — Admin passes all
three checks, Analyst only passes `is_analyst`).

### 8b. User List (`/accounts/users/` — Admin only)

Shows every account with role badge, last login. "Edit" opens the **Django admin** change
form for that user (not a custom page) — this is intentional reuse rather than a gap.

### 8c. Profile (`/accounts/profile/`)

Each user's own bio, avatar, and email-notification preference (`UserProfile` model — kept
as a separate table from `User` so the core authentication table stays lean and fast for
every login check).

### 8d. Security features worth mentioning to your supervisor

- **Login history with GeoIP** (`LoginHistory` model) — every login attempt records IP,
  approximate location, device, and whether it's flagged suspicious (e.g., impossible
  travel — logging in from Lagos and then Tokyo 10 minutes later)
- **TOTP Two-Factor Authentication** (`TwoFactorAuth` model) — optional app-based 2FA with
  backup codes, can be enforced per-role
- **Rate-limited login** — 10 attempts/minute per IP via `django-ratelimit`, to resist
  brute-force attacks
- **Forced password change** (`must_change_password` flag) — new accounts must change
  their password on first login

---

## 9. How the pieces connect — the story you tell in your defense

> "A suspicious access pattern is detected and logged as a `MonitoringEvent` (or directly
> as a `SuspiciousActivity` if it's a record-access anomaly). If it's severe enough, an
> `Alert` is raised. The Risk Engine continuously scores all open threats into a single
> defensible 0–10 risk number using an auditable, non-ML formula. If the alert is serious,
> analysts escalate it into a formal `Incident` that follows the NIST IR lifecycle with a
> timestamped timeline. Meanwhile, the Compliance module independently and continuously
> checks whether the hospital's actual security controls (encryption, access policies,
> backups) meet HIPAA/NDPR/ISO requirements — that's a separate axis from 'are we under
> attack right now.' Every single action anyone takes anywhere in the system — viewing a
> record, acknowledging an alert, running a compliance check — is permanently and
> tamper-evidently recorded in the Audit Log, which cannot be edited or deleted even by an
> administrator. Finally, all of this can be exported as PDF evidence via the Reports
> module for regulators or hospital leadership."

That's the one-paragraph version. Each section above gives you the field-level detail to
back it up if your supervisor drills into any specific page.
