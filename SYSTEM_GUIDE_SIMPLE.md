# HealthSec — Plain English Guide for Non-Technical Users

> **What This System Does**: Watches your hospital's computers to catch security problems and keep patient data safe.

---

## **The One-Line Story**

Your hospital has computers that store patient information. HealthSec is like a security guard that watches those computers 24/7, spots suspicious activity, checks if you're following government rules, and tells the right person when something's wrong.

---

## **What Problem Does It Solve?**

1. **Attacks happen fast** — A hacker might steal patient data in seconds. You need software that catches it before humans can react.
2. **You have to follow rules** — HIPAA, NDPR, ISO 27001. HealthSec automatically checks if you're following them.
3. **People do dumb things** — Employees accidentally leave data exposed or access files they shouldn't. HealthSec flags that.
4. **You need proof for audits** — When a regulator asks "Who accessed what and when?" HealthSec has a record of everything.

---

## **The 5-Minute Walkthrough**

### **Page 1: The Dashboard (Front Door)**

When you log in, you see big colorful numbers:

- **Threats Today** = Real attack attempts detected. Usually 100+.
- **Critical Alerts** = Serious problems needing attention NOW. Usually 10-50.
- **Compliance Score** = Percentage of hospital rules being followed. Target: 100%.
- **Open Incidents** = Security problems under investigation. Usually 1-5.
- **Suspicious Access** = Staff accessing files oddly (after hours, bulk downloads). Usually 100-200.
- **Active Users** = Staff logged in today. Usually 3-10 in demo.
- **Vulnerabilities** = Software bugs that could be exploited. Usually 20-50.

---

### **Page 2: Monitoring (Watch Your Systems)**

Answers: **"What's happening on my computers right now?"**

- **System List** — All major hospital systems (patient portal, imaging, pharmacy). Shows status (ACTIVE/OFFLINE).
  
- **Recent Events** — Log of what happened (logins, file access, downloads). Shows time, who, what system, suspicious flag.

- **Suspicious Activity** — The "weird stuff" tab. Staff at 3 AM. Bulk downloads. New location logins.

---

### **Page 3: Risk Engine (Scoring the Danger)**

Answers: **"How risky is my system right now?"**

Calculates a **Risk Score** 0-10 based on:
- Active attacks happening
- Unpatched software bugs
- How many sensitive files are accessible
- Who has access they shouldn't have

Risk Score meaning:
- **0-3** = Safe
- **4-6** = Caution
- **7-10** = Emergency

Shows:
- **Vulnerabilities** — Software bugs (CVE numbers). Mark "Patched" when fixed.
- **Threat Intelligence** — Known attacks being watched.

---

### **Page 4: Compliance (Following the Rules)**

Answers: **"Are we following HIPAA/NDPR/ISO 27001?"**

For each rule:
- **Automated** check (computer verified?)
- **Manual** check (human verified?)
- **Status** (Compliant ✓ or Not ✗)

Example:
> **Rule**: "All patient access must be logged."
> **Status**: Compliant ✓
> **Evidence**: 1,247 access logs recorded, all with user ID and timestamp.

---

### **Page 5: Alerts & Incidents (Problems and Responses)**

**Alerts** = Automatic notifications from system.
- **Status**: NEW → ACK (acknowledged) → RESOLVED (fixed).
- **Severity**: CRITICAL (urgent) → HIGH → MEDIUM → LOW (informational).

**Incidents** = Official investigations.
- **Phase**: Detection → Containment → Eradication → Recovery → Post-Incident → Closed.

Workflow:
1. Alert triggered
2. Human opens Incident
3. IT investigates (phase changes)
4. Fixed → Closed

---

### **Page 6: Audit Log (Proof It Happened)**

Answers: **"I need to prove to a regulator what happened on June 5th."**

Permanent, unforgeable record of:
- Who logged in/out
- Who accessed which patient records
- Who changed compliance settings
- When alerts were triggered

Nobody can delete or fake audit logs (encrypted, tamper-proof).

---

### **Page 7: Reports (Making Cases)**

Generate PDFs:
1. **Risk Report** — "Here's our risk score, why, and our plan."
2. **Compliance Report** — "We're 87% compliant, fixing the rest."

Each report is timestamped and signed.

---

## **The Security Model (Who Can See What?)**

| Role | Can See | Can Do |
|------|---------|--------|
| **VIEWER** | Dashboards, read-only | Read only |
| **ANALYST** | + Alerts, suspicious activity | Mark alerts reviewed |
| **COMPLIANCE** | + All compliance checks | Upload evidence, update status |
| **ADMIN** | Everything | Manage users, settings |

---

## **What Data Does It Collect?**

**Real data** (hospital operations):
- Patient access logs: "Alice accessed John Doe's record on June 16 at 2:15 PM."
- System logins: "Dr. Smith logged into imaging from IP 192.168.1.50."
- File access: "Someone downloaded 500 patient records."

**Threat intelligence** (attack data):
- Known attack patterns
- CVE database (software hole register)
- Real-world attack statistics

**Compliance data** (audit trail):
- Who changed what rule, when
- What evidence was uploaded

---

## **What Does It Catch?**

1. **Insider threats** — Staff accessing files they shouldn't.
2. **External attacks** — Hackers trying to break in.
3. **Compliance failures** — You're not following regulations.
4. **Accidents** — Good people doing dumb things.

---

## **Real Example: The 3-Day Incident**

**Monday 9 AM**: 500 failed logins in 1 minute (brute force attack).
→ HealthSec creates CRITICAL ALERT.
→ Page shows **Threats Today: +1**.

**Monday 10 AM**: You create INCIDENT.
→ Phase = **Detection**.

**Monday 2 PM**: IT blocks the attacker's IP.
→ Phase = **Containment**.

**Monday 4 PM**: IT patches the vulnerability.
→ Phase = **Eradication**.

**Tuesday 9 AM**: Patch verified working.
→ Phase = **Recovery**.

**Tuesday 10 AM**: Post-mortem written.
→ Phase = **Post-Incident**.

**Wednesday**: Incident **Closed**.

Result: Complete proof for regulators showing detection, response, and learning.

---

## **For Your Supervisor: The Value**

1. **Real-time visibility** — See attacks in minutes, not months.
2. **Automated compliance** — Prove HIPAA/NDPR compliance in seconds, not days.
3. **Audit proof** — Cryptographically signed records when regulators ask.

**ROI**: One $1M breach avoided pays for years of the system.

---

## **Common Questions**

**Q: Does it slow down hospital computers?**
A: No. It's a watcher, like a security camera.

**Q: What if we disagree with a "suspicious" flag?**
A: Mark it resolved. System learns.

**Q: Can patients see this?**
A: No. IT/Compliance only.

**Q: What if the hacker hacks HealthSec?**
A: Audit logs are encrypted and immutable. Also, 2FA (password + phone code) protects logins.

**Q: Do I need IT expertise?**
A: No. 30-minute learning curve.

---

## **Terminology Decoder**

| Term | Meaning |
|------|---------|
| **PHI** | Patient Health Information (what we're protecting) |
| **CVE** | Known software bug (CVE-2024-12345 = "there's a hole, patch it") |
| **HIPAA** | US law: keep records safe and log access |
| **Vulnerability** | Software bug attackers could exploit |
| **Threat** | Actual attack or attacker |
| **Alert** | System says "something bad might be happening" |
| **Incident** | Official investigation |
| **Compliance** | Following rules (0-100%) |
| **Audit Trail** | Unforgeable "who did what and when" record |
| **2FA** | Password + phone code (harder to hack) |
| **Brute Force** | Attacker tries 10,000 passwords |
| **SQL Injection** | Attacker tricks database into giving secrets |
| **Exfiltration** | Stealing and sneaking out data |
| **Ransomware** | Locks files, demands $100K to unlock |

---

**Bottom line**: HealthSec is the bouncer at the hospital's front door. Stops bad guys, makes sure good guys follow rules, keeps permanent proof of everything.

