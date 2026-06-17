# HealthSec CRIC HMS — Complete "How to Use" Guide

**For:** Supervisors, Defense Day, Self-Understanding  
**Level:** Non-Technical Explanation + Detailed Breakdown  
**Updated:** June 2026

---

# TABLE OF CONTENTS

1. [Dashboard](#1-dashboard-main-landing-page)
2. [Monitoring Module](#2-monitoring-module)
3. [Risk Engine Module](#3-risk-engine-module)
4. [Compliance Module](#4-compliance-module)
5. [Alerts & Incidents Module](#5-alerts--incidents-module)
6. [Reports Module](#6-reports-module)
7. [Audit Log](#7-audit-log)
8. [User Profile](#8-user-profile)
9. [Admin Panel](#9-admin-panel)

---

---

# 1. DASHBOARD (Main Landing Page)

## 📊 What Is This Page?

**Simple Explanation:**
This is your command center. It's like a hospital triage board — at a glance, you see all the critical information about your healthcare system's security and compliance. You don't have to dig through reports; everything important is right here.

**Technical Explanation:**
The Dashboard aggregates real-time KPI (Key Performance Indicator) metrics from all 7 modules (Monitoring, Risk Engine, Compliance, Alerts, Incidents, Audit, Reports) and displays them with charts showing trends.

---

## 🔢 Top Metrics (KPI Cards)

### 1️⃣ THREATS DETECTED
**What It Shows:** Number of real cybersecurity attacks detected in your system

**Simple:** This is how many actual hacking attempts, scans, or attacks the system has seen.

**Why It's Important:** 
- High number = Your healthcare system is being targeted
- You need to know if attacks are increasing or decreasing
- Helps you justify spending money on security

**What It Means:**
- 1,000 = We've detected 1,000 real network attacks (from NSL-KDD dataset)
- These include DOS attacks, network scans, unauthorized access attempts
- NOT false alarms — real data from actual cybersecurity research

**Where It Comes From:** Real NSL-KDD cybersecurity dataset (University of New Brunswick)

**Action:** Click "View All" → See threat list, details, source IPs, severity

---

### 2️⃣ CRITICAL ALERTS
**What It Shows:** How many urgent security problems need immediate attention

**Simple:** These are warnings that say "FIX THIS NOW." Not later — now.

**Parameters:**
- **Count (e.g., 46)** = 46 alerts need action
- **Status = "Open"** = Still waiting for someone to fix it
- **Status = "Unresolved"** = Haven't been acknowledged yet

**Why It's Important:**
- CRITICAL = Could compromise patient data or shut down systems
- HIGH = Could be exploited if not fixed soon
- If this number is high, you're under attack right now

**Examples of Critical Alerts:**
- "Malware detected on EHR server"
- "Unauthorized access to patient database"
- "Encryption key compromised"

**Action:** Click → See alert details, who reported it, what to do next, mark as acknowledged

---

### 3️⃣ COMPLIANCE SCORE
**What It Shows:** Percentage of healthcare regulations you're currently following

**Simple:** Think of it like a report card. 40.8% = You're following 40.8% of required rules.

**Parameters:**
- **40.8%** = You're compliant with 40.8% of HIPAA, NDPR, ISO 27001 requirements
- **HIPAA** = US healthcare privacy law
- **NDPR** = Nigerian data protection rule
- **ISO 27001** = International information security standard

**Why It's Important:**
- Less than 80% = You could face fines, lawsuits, license suspension
- This is what regulators check during audits
- This shows if you're protecting patient data properly

**What "Compliant" Means:**
- You have evidence that you're following that rule
- You have documentation, logs, procedures proving it
- Auditors can verify it

**Action:** Click → See which rules you're failing, what to fix, upload evidence to fix them

---

### 4️⃣ OPEN INCIDENTS
**What It Shows:** How many security incidents are actively being handled

**Simple:** These are confirmed attacks that your team is currently investigating and fixing.

**Parameters:**
- **3** = 3 incidents in progress
- **Active response** = Team is working on them right now
- **Phases:** Detection → Analysis → Containment → Eradication → Recovery → Closed

**Why It's Important:**
- Shows you're handling attacks systematically (not just ignoring them)
- Shows incident response maturity (follows NIST standard)
- If this stays high too long, your team is overwhelmed

**Action:** Click → See each incident, its status, assigned analyst, root cause

---

### 5️⃣ SUSPICIOUS ACCESS
**What It Shows:** Number of unusual access patterns detected (unusual logins, unusual times, unusual locations)

**Simple:** When someone accesses patient data at 3 AM, or from a weird location, it's flagged here.

**Parameters:**
- **159** = 159 flagged events
- **"Flagged events today"** = Happened in the last 24 hours

**Why It's Important:**
- Could indicate insider threat (employee stealing data)
- Could indicate hacked credentials (attacker using stolen password)
- Compliance requires monitoring who accesses patient data

**Action:** Click → See suspicious activities list, mark as "resolved" if it's legitimate

---

### 6️⃣ ACTIVE USERS
**What It Shows:** How many unique users logged in and performed actions today

**Simple:** Count of staff members who actually used the system.

**Parameters:**
- **1** = Only 1 person logged in today
- **"Logged in today"** = Performed at least one action

**Why It's Important:**
- Shows system usage
- Too low = System not being used
- Helps with audit trail (who was doing what)

**Action:** Used for reporting who accessed what data

---

### 7️⃣ OPEN VULNERABILITIES
**What It Shows:** Security weaknesses that haven't been fixed yet

**Simple:** Bugs in software or misconfigurations that hackers could exploit. Like leaving a door unlocked.

**Parameters:**
- **40** = 40 known security weaknesses
- **"Unpatched / open"** = Haven't been fixed yet
- **CVSS Score** = How dangerous each one is (1-10 scale)

**Why It's Important:**
- Every open vulnerability = Potential entry point for attackers
- You need to prioritize which ones to fix first
- Regulators want to see your patching plan

**Action:** Click → See vulnerability list, CVSS scores, fix status, timeline to patch

---

### 8️⃣ HEALTHCARE SYSTEMS
**What It Shows:** Physical/logical IT systems in your hospital

**Simple:** Count of important systems you're monitoring (EHR, PACS, Lab, etc.)

**Parameters:**
- **6** = 6 systems being monitored
- **"Monitoring active"** = Currently protected and logged

**Why It's Important:**
- Each system could contain patient data
- Need to protect all of them
- Compliance requires knowing what you have

**Action:** Click "System List" → See each system, what data it contains, status

---

## 📈 Charts (Visual Analytics)

### THREAT ACTIVITY TIMELINE (Line Chart)
**What It Shows:** How many attacks happened each day for the past 30 days

**Simple:** Shows if attacks are increasing or decreasing over time.

**How to Read It:**
- X-axis (bottom) = Date (05-15, 05-22, 05-28, etc.)
- Y-axis (left) = Number of threats
- Line going up = More attacks on that day
- Line going down = Fewer attacks on that day
- Peak on 06-15 = That day had the most attacks

**Why It's Important:**
- Spot trends (is attack volume increasing?)
- Identify attack patterns (Mondays busier than weekends?)
- Show if your defenses are working (lower line = success)

**What to Do:**
- If line keeps going up → You're under sustained attack, need help
- If line goes down → Your fixes are working
- Show this to executives to justify security spending

---

### ALERT SEVERITY (Donut Chart)
**What It Shows:** Breakdown of open alerts by severity level

**Simple:** "How many red flags are critical vs. medium vs. low?"

**Chart Colors:**
- **Red = CRITICAL** (Must fix immediately)
- **Orange = HIGH** (Fix today)
- **Yellow = MEDIUM** (Fix this week)
- **Green = LOW** (Fix when you have time)

**How to Read It:**
- A big red section = Many critical alerts (BAD)
- Small red section = Few critical alerts (GOOD)
- Mostly green = System is healthy

**Why It's Important:**
- Helps prioritize what to fix first
- If mostly red/orange → You're in trouble, need escalation
- If mostly green → You're managing well

---

## 🔄 How to Use the Dashboard

### Step 1: Check KPI Cards (30 seconds)
1. **Login** → You land on Dashboard
2. **Read the numbers:**
   - Threats Detected: 1,000 ✓
   - Critical Alerts: 46 (Action needed)
   - Compliance Score: 40.8% (Below 80%, need work)
   - Open Incidents: 3 (Being handled)

### Step 2: Spot Problems (1 minute)
- **Red flags:** High alerts, low compliance, many open vulns
- **Green flags:** Low threats, high compliance, all systems active

### Step 3: Drill Down
- Click on any metric to see details
- Click charts to see full data
- Click "View All" buttons to see complete lists

### Step 4: Take Action
- **Alerts:** Acknowledge and assign to analyst
- **Incidents:** Check status, see what analyst is doing
- **Compliance:** See what rules you're failing, fix them
- **Vulnerabilities:** Prioritize by severity

---

### Real Example: "We're Under Attack"

**Scenario:** You see:
- Threats Detected: 1,000
- Critical Alerts: 46 (all NEW)
- Compliance Score: 40.8%
- Open Incidents: 3
- Threat Timeline: Big spike on 06-15

**What It Means:**
Your healthcare system is experiencing a coordinated attack. Multiple alerts fired, incidents are being handled.

**What You Do:**
1. Click "Critical Alerts" → See "Malware detected on EHR"
2. Click alert → Assigned to analyst@healthsec.local
3. See it was detected 1 hour ago
4. See it's in ACKNOWLEDGED status (team is aware)
5. Go to Incidents → See it's in ANALYSIS phase
6. Email analyst: "Status update?"

---

---

# 2. MONITORING MODULE

## 📡 What Is This Module?

**Simple:** Monitor who's accessing patient data and when. Catch unusual behavior.

**Technical:** Tracks healthcare system access events and flags suspicious patterns.

---

## 🖥️ Page 1: Healthcare Systems List

### What You See

A table showing all your monitored healthcare systems:

| System Name | Type | Status | Contains PHI | Actions |
|---|---|---|---|---|
| EHR Central | EHR | ACTIVE | ✓ Yes | View Details |
| PACS Hospital | PACS | ACTIVE | ✓ Yes | View Details |
| Lab System | Lab | ACTIVE | - No | View Details |
| Pharmacy | Pharmacy | INACTIVE | ✓ Yes | View Details |

### Each Column Explained

**System Name:** What it's called (EHR Central = Electronic Health Record system)

**Type:** 
- EHR = Electronic Health Records (patient medical charts)
- PACS = Picture Archiving (X-rays, CT scans)
- Lab = Lab results system
- Pharmacy = Medicine dispensing system

**Status:**
- ACTIVE = Currently operational, being monitored
- INACTIVE = Shut down or not monitoring right now

**Contains PHI:**
- ✓ Yes = Holds patient medical information (very important to protect)
- - No = Just operational data (less critical)

**Actions:**
- Click "View Details" → See:
  - What data this system stores
  - Recent access events
  - Suspicious activities
  - Risk score
  - Compliance status

### Why It's Important

You need to know:
- How many systems you have
- Which ones have patient data
- If they're all still working
- What each one does

### Real Example

**Scenario:** PACS Hospital shows INACTIVE
- Question: Why is PACS down?
- Action: Click Details → See last activity was 2 days ago
- Next: Contact IT — "Did we intentionally shut down PACS?"

---

## 📋 Page 2: Healthcare System Details

### What You See When You Click a System

#### Top Section: System Information
```
┌─────────────────────────────────────────────┐
│ EHR Central                                  │
│ Type: Electronic Health Record System        │
│ Status: ✓ ACTIVE (since 05-15-2026)         │
│ Contains Patient Data (PHI): YES             │
│ Risk Score: 7.2/10 (HIGH)                    │
│ Last Activity: 2 minutes ago                 │
└─────────────────────────────────────────────┘
```

**Each Field Explained:**
- **Type:** What the system does
- **Status:** Running or down?
- **Contains PHI:** Does it hold patient medical records?
- **Risk Score:** 0-10 scale. High = Lots of threats against this system
- **Last Activity:** When was it last used?

#### Middle Section: Data Assets on This System

| Asset | Classification | Records | Sensitivity |
|---|---|---|---|
| Patient Demographics | PHI | 5,000+ | HIGH |
| Medical History | PHI | 5,000+ | CRITICAL |
| Lab Results | PHI | 10,000+ | HIGH |
| Appointment Notes | NON-PHI | 20,000+ | LOW |

**Classification:**
- PHI = Protected Health Information (regulated, fines if leaked)
- NON-PHI = General information (not regulated)

**Sensitivity:** How bad if this data leaks?
- CRITICAL = Lives at risk, massive fines
- HIGH = Serious privacy breach
- LOW = No immediate danger

#### Bottom Section: Recent Access Events

| User | Date/Time | Action | Source IP | Status |
|---|---|---|---|---|
| nurse@hospital.local | 06-17 14:32 | View Patient Record #2341 | 192.168.1.50 | ✓ Normal |
| doctor@hospital.local | 06-17 13:15 | Export Report | 192.168.1.75 | ⚠️ Suspicious |
| admin@hospital.local | 06-17 03:00 | Database Backup | 192.168.1.100 | ⚠️ Flagged (3 AM) |

**What Each Column Means:**
- **User:** Who accessed the system?
- **Date/Time:** When?
- **Action:** What did they do?
- **Source IP:** Which computer/network location?
- **Status:** Normal or suspicious?

**Why This Matters:**
- Doctor accessing patient records at 3 AM = Suspicious
- Exporting all reports suddenly = Might be data theft
- Multiple logins from different IPs = Hacked credentials?

### Why This Page Is Important

You need to know:
- What data is on each system
- How sensitive is that data?
- Who's accessing it?
- Are access patterns normal?

### What You Can Do

1. **View System Details** → Click on any system
2. **See Data Assets** → What's stored there?
3. **Review Access Events** → Who accessed what and when?
4. **Flag Suspicious Activity** → Mark weird access as suspicious
5. **Check Risk Score** → Is this system under attack?

---

## 🚨 Page 3: Suspicious Activity List

### What You See

A list of flagged access events that look unusual:

```
⚠️ HIGH SEVERITY - Unresolved
User: admin@hospital.local
Activity: Database access from unusual location (10.50.50.1)
When: 06-16 02:15 AM
Patient Records Accessed: 147 records
Status: UNRESOLVED
Action: [Mark Resolved]
```

### Each Field Explained

**Severity:** How concerning is this?
- CRITICAL = Definitely suspicious, investigate immediately
- HIGH = Probably suspicious, needs review
- MEDIUM = Might be legitimate, double-check
- LOW = Probably nothing, but logged

**Activity:** What happened?
- "Database access from new location" = Employee working from home?
- "Mass export of patient records" = Possible data theft
- "Login attempt failed 10 times" = Attacker trying to guess password
- "Access outside business hours" = Employee working late, or intruder?

**Who:** Which employee/account?

**When:** Date and time of the activity

**What They Did:** Specific action (access, export, delete, etc.)

**Records Affected:** How many patient records touched?

**Status:**
- UNRESOLVED = Admin hasn't reviewed it yet
- REVIEWED = Admin looked at it
- FALSE ALARM = Turned out to be legitimate
- CONFIRMED THREAT = Was definitely an attack

### Why This Page Is Important

This is where you catch:
- **Data theft** — Someone exporting all patient records
- **Insider threats** — Employee accessing data they shouldn't
- **Hacked accounts** — Attacker using stolen password
- **Compliance violations** — Unauthorized access to PHI

### What You Can Do

1. **Review Flag** → Click to see full details
2. **Investigate** → Ask: Is this normal? Did this person usually work at this time?
3. **Mark Resolved** → Click if it's legitimate (employee working late, etc.)
4. **Escalate** → If suspicious, report to security team
5. **Review Trend** → If same person keeps flagging, dig deeper

### Real Example

**Scenario:** You see:
- "Massive export of patient records (2,000 files)"
- User: billing_clerk@hospital.local
- When: 03:00 AM (middle of night)
- Status: UNRESOLVED

**What to Do:**
1. Click it → See it was from random IP address (not normal location)
2. Call billing clerk → "Did you access records at 3 AM last night?" (They'll say no)
3. Escalate → "Possible data breach, billing clerk's password compromised"
4. Security team → Reset password, check what was exported
5. Mark as THREAT → Will show in audit trail

---

## 🎯 How to Use Monitoring Module

### Daily Workflow (5 minutes)
1. **Check Systems List** → Are all systems ACTIVE?
2. **Check Suspicious Activity** → Any new flags?
3. **Review if Needed** → Call employee if something looks off

### When Suspicious Activity Appears
1. **Click the alert**
2. **Read details:** User, time, what they did
3. **Call the employee:** "Hey, did you access the EHR at 3 AM?"
4. **Get response:**
   - "Yes, I was catching up on notes" → Mark RESOLVED
   - "No, I was asleep" → CONFIRM THREAT, escalate to IT
5. **Document** → Mark as resolved or escalated

### Why This Matters for Compliance
- **HIPAA §164.312(d):** Access logs required
- **NDPR Article 28:** Audit trails for data access
- **ISO 27001 A.12.4.1:** Event logging and monitoring

---

---

# 3. RISK ENGINE MODULE

## ⚠️ What Is This Module?

**Simple:** Combines threat data, vulnerabilities, and sensitive data to give you a single RISK SCORE (0-10).

**Technical:** Real-time risk assessment using NSL-KDD cybersecurity dataset.

---

## 🎯 Page 1: Risk Dashboard

### What You See

**Risk Score Display (Big)**
```
┌─────────────────────────────┐
│                              │
│         RISK SCORE           │
│                              │
│            7.2/10            │
│                              │
│         🔴 HIGH RISK         │
│                              │
└─────────────────────────────┘
```

### Risk Score Meaning

| Score | Level | Meaning | Action |
|---|---|---|---|
| 0-2 | 🟢 LOW | System is safe, continue monitoring | None needed |
| 3-5 | 🟡 MEDIUM | Some vulnerabilities exist | Plan fixes |
| 6-8 | 🔴 HIGH | Active threats, needs attention | Fix this week |
| 9-10 | 🔴🔴 CRITICAL | Under attack or major breach risk | FIX NOW |

### What Goes Into Risk Score?

The score combines **3 factors:**

#### Factor 1: Threat Count (How many active attacks?)
- 0 attacks = 0/10 score
- 500 attacks = 5/10 score
- 1000+ attacks = 10/10 score

#### Factor 2: Vulnerabilities (How many security holes?)
- 0 unpatched vulns = 0/10 score
- 3 unpatched vulns = 6/10 score
- 10+ unpatched vulns = 10/10 score

#### Factor 3: PHI Assets (How much patient data?)
- 0 systems with patient data = 0/10 score
- 1 system with patient data = 5/10 score
- 3+ systems with patient data = 10/10 score

### How It's Calculated

```
Risk Score = (Threat Score + Vulnerability Score + PHI Score) / 3
Example: (8 + 5 + 6) / 3 = 6.3/10 (HIGH RISK)
```

### Why This Matters

- **0-2:** Sleep well, system is protected
- **3-5:** Review your security plan
- **6-8:** Urgent action required, allocate resources
- **9-10:** Emergency, activate incident response

---

## 📊 Page 2: Threat Activity Timeline

### What It Shows

Line chart with dates on bottom and threat count on left:

```
Threats
1,200 |                    ╱╲
  800 |          ╱╲      ╱  ╲
  400 |    ╱╲  ╱  ╲    ╱    ╲
    0 |_╱__╲╱____╲__╱______╲_
      05-15 05-22 05-28 06-03 06-15
```

### How to Read It

- **X-axis:** Dates (left to right = older to newer)
- **Y-axis:** Number of threats (bottom to top = low to high)
- **Line going up:** More attacks on that day
- **Line going down:** Fewer attacks
- **Spike:** Peak day with most attacks

### What It Tells You

- **Steady high line:** Sustained attack, not getting better
- **Line trending down:** Your defenses are working, threats decreasing
- **Spike peaks:** Day you got hit hardest
- **Flat line:** No active threats (good news)

### Why This Matters

You can show this to:
- **Board:** "Here's proof we were under attack on June 15"
- **Auditors:** "Our threats have decreased 40% since we deployed new firewall"
- **Budget committee:** "This spike shows why we need better security"

---

## 🗺️ Page 3: Risk Heatmap (7 days × 24 hours)

### What It Shows

Grid showing which days and hours have most attacks:

```
       00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23
Mon    🟢🟢🟡🟢🟢🟢🟢🟡🟡🟡🔴🔴🟡🟡🟡🟡🟡🟡🟡🟢🟢🟢🟢🟢
Tue    🟢🟢🟢🟢🟢🟢🟢🟡🟡🟡🟡🔴🔴🔴🟡🟡🟡🟡🟢🟢🟢🟢🟢
Wed    🟢🟢🟢🟢🟢🟢🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟢🟢🟢🟢🟢
Thu    🟢🟢🟢🟢🟢🟢🟡🟡🟡🟡🔴🔴🔴🟡🟡🟡🟡🟢🟢🟢🟢🟢
Fri    🟢🟢🟢🟢🟢🟢🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟢🟢🟢🟢🟢
Sat    🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢
Sun    🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢

🟢 Green = No attacks
🟡 Yellow = Few attacks
🔴 Red = Many attacks
```

### What It Tells You

**Attack Pattern Recognition:**
- **Red cluster at 10-14h on weekdays** = Attackers work 9-5
- **Green weekends** = Attackers don't attack on weekends
- **Red on Mondays-Thursdays** = Coordinated attack campaign
- **Red at 3 AM** = Automated attacks (bots)

### Why This Matters

- **Pattern spotting:** Identify attack campaigns
- **Resource planning:** More security staff during peak attack hours
- **Incident response:** During red hours, have team on standby

---

## 📝 Page 4: Threat List

### What You See

Table of all detected threats:

| Threat Type | Severity | Detected | Source IP | Status |
|---|---|---|---|---|
| DOS Attack | 8/10 | 06-16 14:32 | 10.50.50.1 | OPEN |
| Network Scan | 5/10 | 06-16 13:15 | 10.50.50.2 | OPEN |
| Brute Force | 6/10 | 06-16 12:00 | 10.50.50.3 | MITIGATED |
| Malware | 10/10 | 06-15 02:15 | 10.50.50.4 | OPEN |

### Each Column Explained

**Threat Type:**
- **DOS (Denial of Service):** Attacker floods server with traffic, crashes it
- **Brute Force:** Attacker tries many passwords to guess your login
- **Network Scan:** Attacker mapping your network, finding vulnerabilities
- **Malware:** Malicious software trying to run on your systems
- **Data Exfiltration:** Attacker stealing data

**Severity (0-10 scale):**
- 10 = Will cause severe damage if not blocked
- 8 = Will cause significant damage
- 5 = Will cause some damage
- 1 = Minimal threat

**Detected:** When did system catch it?

**Source IP:** Where is the attack coming from?
- Real source IP (in this case 10.x.x.x = safe demo range)
- In production, would show actual attacker IP

**Status:**
- OPEN = Still active, not yet blocked
- MITIGATED = Blocked, threat neutralized
- CLOSED = Completely handled

### What You Can Do

1. **Click a threat** → See full details, description
2. **Review:**
   - What kind of attack?
   - How dangerous?
   - When did it happen?
   - Where from?
3. **Escalate if needed** → Email security team
4. **Track over time** → Are certain IPs attacking repeatedly?

---

## 🔧 Page 5: Vulnerability List

### What You See

List of known security holes:

| CVE ID | Title | CVSS Score | Affected System | Status | Fix Deadline |
|---|---|---|---|---|---|
| CVE-2024-1234 | SQL Injection in Portal | 8.5/10 | EHR Central | OPEN | 07-15 |
| CVE-2024-1235 | Authentication Bypass | 9.0/10 | Lab System | OPEN | 07-01 |
| CVE-2024-1236 | Cross-Site Scripting | 6.2/10 | Pharmacy | PATCHED | 06-30 ✓ |

### Each Column Explained

**CVE ID:** Official identifier for this security hole
- Format: CVE-YEAR-NUMBER
- Example: CVE-2024-1234

**Title:** What's the vulnerability?
- SQL Injection = Attacker can run database commands
- Authentication Bypass = Attacker can login without password
- Cross-Site Scripting = Attacker can run code in your browser

**CVSS Score (0-10):**
- 9-10 = CRITICAL, patch immediately
- 7-8 = HIGH, patch this week
- 5-6 = MEDIUM, patch this month
- 1-4 = LOW, patch when possible

**Affected System:** Which system has this hole?

**Status:**
- OPEN = Not yet fixed
- PATCHED = Software update applied

**Fix Deadline:** By when must it be fixed?

### Why This Matters

Every unpatched vulnerability = Potential entry for attackers.

**Risk:**
- 1 vulnerability with CVSS 9.0 = Very dangerous
- 20 vulnerabilities with CVSS 5.0 = Less critical but still bad
- 0 vulnerabilities = Excellent (unrealistic)

### What You Can Do

1. **Review list** → Which are OPEN?
2. **Prioritize by CVSS** → Fix 9.0 first
3. **Check deadline** → Any overdue?
4. **Coordinate with IT:** "Can we patch these by July 15?"
5. **Track progress** → Move from OPEN to PATCHED

### Real Example

**Scenario:** You see:
- CVE-2024-1234 = SQL Injection, CVSS 8.5, EHR Central, OPEN, Due 07-15
- Today is 06-20

**What to Do:**
1. Email IT: "We have 25 days to patch CVE-2024-1234"
2. Ask: "Do we have the patch?"
3. Ask: "Can you test it?"
4. Ask: "When can we deploy?"
5. Track: Once patched, mark as PATCHED, provide patch date

---

## 🎯 How to Use Risk Engine

### Daily (1 minute)
1. Check Risk Score → Is it 6+? (if yes, needs attention)
2. Check Threat Timeline → Is line going up?
3. Check Vulnerabilities → Any new ones? Any overdue fixes?

### Weekly (10 minutes)
1. Review Threat List → Any patterns?
2. Review Vulnerability List → Plan patches
3. Review Heatmap → Identify attack patterns
4. Executive report → "Risk trending up/down"

### For Defense Day
1. Show Risk Score: "This is how much risk we're under (7.2/10 = HIGH)"
2. Show Threat Timeline: "Here's proof we detected 1,000 real attacks"
3. Show Heatmap: "Attacks mostly happen 10 AM - 2 PM weekdays"
4. Show Vulnerabilities: "We track all security holes and patch by deadline"

---

---

# 4. COMPLIANCE MODULE

## ✅ What Is This Module?

**Simple:** Track healthcare regulations (HIPAA, NDPR, ISO 27001) and prove you're following them.

**Technical:** Compliance framework assessment with evidence tracking and control verification.

---

## 🏛️ Page 1: Compliance Summary

### What You See

```
┌─────────────────────────────────────────┐
│         COMPLIANCE POSTURE               │
├─────────────────────────────────────────┤
│                                          │
│  HIPAA         ████████░░░ 92%  46/50    │
│  NDPR          ██████░░░░░░░ 60% 18/30   │
│  ISO 27001     ███████░░░░░ 70%  35/50   │
│                                          │
│  Overall:      ███████░░░░░░ 74%  99/130 │
│                                          │
└─────────────────────────────────────────┘
```

### Understanding the Percentages

**92% HIPAA Compliant:**
- You're meeting 46 out of 50 HIPAA requirements
- 4 requirements still need work
- This is GOOD (above 80%)

**60% NDPR Compliant:**
- You're meeting 18 out of 30 NDPR requirements
- 12 requirements need work
- This needs improvement (below 80%)

**70% ISO 27001 Compliant:**
- You're meeting 35 out of 50 ISO 27001 requirements
- 15 requirements need work
- This is okay but should improve

**Overall: 74%**
- Average compliance across all frameworks
- **Target:** 80%+ for audit readiness
- **Current:** Below target, need 6 more controls to pass

### Why Each Framework?

**HIPAA (US Healthcare Privacy):**
- Required if: You operate in USA, handle US patient data
- Covers: Patient privacy, data security, breach notification
- Fines: Up to $1.5 million per violation

**NDPR (Nigerian Data Protection):**
- Required if: You operate in Nigeria, handle Nigerian patient data
- Covers: Consent, data retention, data subject rights
- Fines: Up to 2-3% of revenue per violation

**ISO 27001 (International Standard):**
- Required if: International healthcare organization, accredited hospitals
- Covers: Information security management system (ISMS)
- Benefit: Shows professional security standards

### What "Compliant" Means

A control is COMPLIANT if:
- You have documented policy
- You have evidence (logs, procedures, training records)
- You can show auditor proof
- You're consistently following it

**Example:**
- Requirement: "Patient data must be encrypted at rest"
- Compliant proof: Database encryption enabled, encryption key stored securely, key rotation policy documented
- Auditor can verify: Check server config, see encryption enabled ✓

---

## 📋 Page 2: Framework Details (Example: HIPAA)

### What You See

List of all controls under HIPAA:

```
┌─────────────────────────────────┬──────┐
│ Control ID │ Title              │ Status│
├─────────────────────────────────┼──────┤
│ 164.304   │ Security Management│  ✓   │
│ 164.306   │ Security Standards │  ✓   │
│ 164.308   │ Admin Procedures   │  ✓   │
│ 164.310   │ Physical Security  │  ✓   │
│ 164.312   │ Technical Security │  ✗   │
│ 164.314   │ Coordination       │  ✓   │
└─────────────────────────────────┴──────┘

✓ = COMPLIANT (passing)
✗ = NON-COMPLIANT (failing, needs work)
```

### Control ID Explained

**164.304 = HIPAA Security Management Plan:**
- Requirement: "Document your security plan"
- Status: COMPLIANT ✓
- Evidence: You have security_plan.pdf on file

**164.312 = HIPAA Technical Security:**
- Requirement: "Encrypt data, use access controls, audit logs"
- Status: NON-COMPLIANT ✗
- Issue: Audit log not tamper-proof yet
- What to do: Implement SHA256 verification

### What You Can Do

1. **Click any control** → See full requirement text
2. **See status** → Is it passing or failing?
3. **Review evidence** → What proof do you have?
4. **Upload evidence** → If failing, add documentation to fix it
5. **Mark COMPLIANT** → Once fixed, auditor can verify

---

## 🔍 Page 3: Control Detail (Example: "Audit & Accountability")

### What You See

```
┌────────────────────────────────────────────┐
│ HIPAA §164.312(b) - Audit & Accountability│
├────────────────────────────────────────────┤
│                                             │
│ Requirement:                                │
│ "Maintain audit logs of all data access    │
│  and modifications. Logs must be           │
│  protected from tampering."                │
│                                             │
│ Status: ✗ NON-COMPLIANT                    │
│                                             │
│ Failing Because:                            │
│ - Logs not protected from deletion         │
│ - No tamper detection mechanism            │
│ - Retention policy not documented          │
│                                             │
│ Fix Required:                               │
│ 1. Implement immutable logs (append-only)  │
│ 2. Add SHA256 tamper detection             │
│ 3. Document retention policy (7 years)     │
│                                             │
│ Evidence Files:                             │
│ [Upload audit_log_procedure.pdf]           │
│ [Upload tamper_detection_proof.pdf]        │
│ [Upload retention_policy.pdf]              │
│                                             │
│ [✓ Mark Compliant When Ready]              │
└────────────────────────────────────────────┘
```

### Each Section Explained

**Requirement:** What regulation says you must do

**Status:** Are you doing it?
- COMPLIANT ✓ = Yes, doing it
- NON-COMPLIANT ✗ = No, need to fix

**Failing Because:** Why doesn't it pass?
- Lists specific gaps

**Fix Required:** How to fix it?
- Step-by-step action items

**Evidence Files:** Proof you're compliant
- Can upload PDF, documents, screenshots
- Auditor will review these

### Real Example

**Scenario:** HIPAA §164.312(b) showing NON-COMPLIANT

**What It Means:**
"Your audit logs aren't properly protected. Someone could delete or modify them, destroying evidence of who accessed patient data."

**Why It's Critical:**
- Regulators require proof of what happened
- If logs are deleted, you can't prove you didn't leak data
- Fines can be $1.5M+

**How to Fix:**
1. Make logs append-only (can't be deleted or modified)
2. Add SHA256 hash verification (proves tampering)
3. Document how long you keep logs
4. Upload proof to this control
5. Mark as COMPLIANT

**Evidence You'd Upload:**
- Document: "Audit_Log_Immutability_Procedure.pdf"
- Screenshot: Database configuration showing append-only setting
- Document: "Log_Retention_Policy_7years.pdf"

---

## 🎯 How to Use Compliance Module

### Weekly (15 minutes)
1. **Check Compliance Summary** → What's your overall score?
2. **Identify Failing Controls** → Which ones show ✗?
3. **Prioritize:** Fix highest-impact ones first

### When Failing Controls Found

1. **Click the control** → Read full requirement
2. **Understand requirement** → What must you do?
3. **Gather evidence:**
   - Policy documents
   - Configuration screenshots
   - Logs showing compliance
   - Training records
4. **Upload evidence** → To that control
5. **Mark COMPLIANT** → When ready
6. **Auditor verifies** → During audit, they'll check

### For Audit Preparation (1 month before)

1. **Review Compliance Summary** → Target 80%+ score
2. **Fix failing controls** → Get all to COMPLIANT status
3. **Document everything** → Upload evidence
4. **Brief team** → Everyone knows their role
5. **Practice audit walkthrough** → Simulate auditor questions

### For Defense Day Presentation

1. **Show Summary** → "We're 74% compliant overall"
2. **Show Details** → "HIPAA 92%, NDPR 60%, ISO 27001 70%"
3. **Explain gaps** → "Working on NDPR, fixing by month-end"
4. **Show evidence** → Examples of controls with documentation
5. **Demonstrate process** → Walk through marking a control COMPLIANT

---

---

# 5. ALERTS & INCIDENTS MODULE

## 🚨 What Is This Module?

**Simple:** Manage security warnings and track how you handle them.

**Technical:** Alert generation, NIST incident lifecycle tracking, assignment workflows.

---

## 📬 Page 1: Alert List

### What You See

Table of all security alerts:

```
STATUS   SEVERITY  ALERT TITLE                CREATED    ASSIGNED TO     ACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 NEW   CRITICAL  Malware on EHR Server      6/16 14:32 analyst1@hs.com  [ACK]
🟠 ACK   HIGH      Unauthorized Access       6/16 13:15 analyst2@hs.com  [RESOLVE]
🟡 ACK   MEDIUM    Password Policy Violated  6/16 12:00 analyst1@hs.com  [RESOLVE]
🟢 RES   LOW       Certificate Expiring       6/15 10:00 —                 [CLOSED]
```

### Status Explained

| Status | Meaning | Color | What to Do |
|---|---|---|---|
| NEW | Just created, nobody acknowledged | 🔴 Red | Review ASAP |
| ACK | Acknowledged by analyst | 🟠 Orange | Analyst working on it |
| RESOLVED | Fixed/closed by analyst | 🟢 Green | Done |

### Severity Explained

| Level | Color | Meaning | Action |
|---|---|---|---|
| CRITICAL | 🔴 Red | Fix immediately, could breach patient data | Drop everything, handle now |
| HIGH | 🟠 Orange | Urgent, needs attention today | Assign to top analyst |
| MEDIUM | 🟡 Yellow | Important, handle this week | Schedule fix |
| LOW | 🟢 Green | Nice to fix, not urgent | Backlog |

### Each Column Explained

**STATUS:** Where is this alert in workflow?

**SEVERITY:** How bad is it?

**ALERT TITLE:** What's the problem?
- "Malware on EHR" = Detected malicious code
- "Unauthorized access" = Someone accessed data they shouldn't
- "Password policy violated" = Weak password used
- "Certificate expiring" = SSL certificate expires soon

**CREATED:** When was alert generated? (6/16 14:32 = June 16, 2:32 PM)

**ASSIGNED TO:** Which analyst is handling it?
- Blank = Unassigned, needs someone
- Shows name = Someone is working on it

**ACTION BUTTONS:**
- [ACK] = Acknowledge ("I see this, will investigate")
- [RESOLVE] = Mark as fixed
- [CLOSE] = Close alert

### What You Can Do

1. **Filter by severity** → "Show only CRITICAL"
2. **Filter by status** → "Show only NEW"
3. **Assign alert** → "Give this to analyst1"
4. **Acknowledge** → "I'm aware of this issue"
5. **Resolve** → "We fixed this issue"
6. **Close** → "Done, archive this"

### Real Example

**Scenario:** You see:
```
🔴 NEW   CRITICAL  Malware on EHR Server   6/16 14:32 (UNASSIGNED)
```

**What to Do:**
1. Click alert → See full details
2. See: "Trojan detected in EHR_backup.exe"
3. Recognize: This is CRITICAL, must handle now
4. Click [ACK] → System acknowledges you saw it
5. Assign to analyst → "Give this to analyst1"
6. Email analyst: "Critical alert, malware on EHR, investigate ASAP"
7. Follow up: Check in 1 hour for status

**After Analyst Fixes It:**
1. Click [RESOLVE] → Mark as fixed
2. See notes from analyst: "Malware removed, cleaned server, rescanned"
3. Verify: Ask analyst for proof (antivirus scan report)
4. Click [CLOSE] → Alert closed, archived for audit trail

---

## 📖 Page 2: Alert Detail

### What You See When You Click an Alert

```
┌──────────────────────────────────────────────┐
│ ALERT #42                                    │
├──────────────────────────────────────────────┤
│                                               │
│ Title: Unauthorized Access to Patient Data  │
│ Severity: CRITICAL                          │
│ Status: ACK (Acknowledged)                  │
│ Created: 06-16 13:15 by system              │
│ Assigned To: analyst1@healthsec.local       │
│                                               │
│ ────────────────────────────────────────────│
│ DETAILS:                                     │
│ ────────────────────────────────────────────│
│                                               │
│ What Happened:                               │
│ Employee accessed 500+ patient records       │
│ without clear business need                  │
│                                               │
│ System: EHR Central                          │
│ Time: 06-16 02:15 AM (unusual hour)         │
│ Records Accessed: 542                        │
│ Patient Impact: 542 patients' data exposed  │
│                                               │
│ Source: Access flagged by monitoring system │
│ (Suspicious Activity Detection)              │
│                                               │
│ ────────────────────────────────────────────│
│ RELATED INCIDENT:                            │
│ ────────────────────────────────────────────│
│ Incident #7 (Phase: ANALYSIS)                │
│                                               │
│ Timeline:                                    │
│ 06-16 13:15 - Alert Created (DETECTION)    │
│ 06-16 13:20 - Analyst1 Acknowledged        │
│ 06-16 13:30 - Incident Created (ANALYSIS)  │
│ 06-16 14:00 - Employee Contacted           │
│ 06-16 14:15 - Employee Admits (got data    │
│              for billing, didn't follow    │
│              proper procedure)              │
│ Pending: Disciplinary review                │
│                                               │
│ ────────────────────────────────────────────│
│ ACTIONS AVAILABLE:                           │
│                                               │
│ [Acknowledge] [Resolve] [Escalate] [Close] │
│                                               │
└──────────────────────────────────────────────┘
```

### Each Section Explained

**Alert ID:** Unique number for tracking

**Title:** Short description of problem

**Severity:** CRITICAL, HIGH, MEDIUM, LOW

**Status:** Where in workflow (NEW, ACK, RESOLVED, CLOSED)

**Created:** When and how alert was triggered

**Assigned To:** Which analyst owns it

**What Happened:** Detailed description of the issue

**System:** Which system was involved (EHR Central, Lab, etc.)

**Time:** When did it occur?

**Records Affected:** How many patient records touched?

**Related Incident:** Is this part of larger incident?
- If yes, shows incident ID and current phase

**Timeline:** Chronological history of actions taken

**Action Buttons:**
- [Acknowledge] = "I see this, investigating"
- [Resolve] = "Issue fixed"
- [Escalate] = "This needs higher management"
- [Close] = "Done, archive alert"

### Real Example

**Scenario:** Alert shows:
- "Unauthorized access to patient data"
- "542 patient records accessed"
- "2:15 AM unusual time"

**Investigation Steps:**
1. **Read alert:** Employee accessed data at 2:15 AM
2. **Check with employee:** "Why at 2:15 AM?"
3. **Response:** "I was working from home, couldn't sleep, reviewing billing info"
4. **Decision:**
   - Valid reason? → Mark RESOLVED
   - Invalid reason? → Escalate to HR/Security
5. **Document:**
   - Analyst adds notes: "Employee admits unauthorized access, no valid business need, referred to HR for disciplinary action"
6. **Mark RESOLVED** → Create incident for follow-up

---

## 🔄 Page 3: Incident List

### What You See

Table of ongoing incidents:

```
INCIDENT # │ ALERT       │ PHASE          │ CREATED   │ ANALYST      │ DAYS OPEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#7         │ Alert #42   │ ANALYSIS       │ 06-16     │ analyst1     │ 1 day
#6         │ Alert #38   │ CONTAINMENT    │ 06-14     │ analyst2     │ 3 days
#5         │ Alert #35   │ ERADICATION    │ 06-12     │ analyst1     │ 5 days
#4         │ Alert #30   │ RECOVERY       │ 06-05     │ analyst3     │ 12 days
#3         │ Alert #15   │ CLOSED         │ 05-28     │ analyst2     │ 20 days
```

### Phase Explained (NIST Lifecycle)

| Phase | Meaning | How Long | What Happens |
|---|---|---|---|
| DETECTION | Alert triggered, confirmed incident | Minutes | System detected threat |
| ANALYSIS | Investigating root cause | Hours | Analyst examines what happened |
| CONTAINMENT | Isolating affected systems | Hours-Days | Stop attack from spreading |
| ERADICATION | Removing threat | Days-Weeks | Delete malware, fix vulnerability |
| RECOVERY | Restoring systems | Days-Weeks | Get systems back to normal |
| CLOSED | Incident complete | — | Post-incident review done |

### Days Open Explained

**1 day:** Just started, in ANALYSIS phase (normal)

**3 days:** In CONTAINMENT, should move to ERADICATION soon (okay)

**5 days:** In ERADICATION, on track (normal)

**12 days:** In RECOVERY, starting to be long (check status)

**20 days:** CLOSED, post-incident review complete (done)

### What You Can Do

1. **Click incident** → See full details
2. **Check phase** → Where is it in resolution?
3. **Review timeline** → What actions have been taken?
4. **Update phase** → Move to next phase when ready
5. **Add notes** → Document actions taken

### Real Example

**Scenario:** You see:
```
Incident #7 - ANALYSIS phase - 1 day old
```

**Check Status:**
1. Click it → See details
2. Analyst notes: "Malware found on EHR, identified it as Trojan.Win32"
3. See actions: "Isolated server, prevented spread, antivirus running"
4. Update phase: "Move to CONTAINMENT once server isolated"

**After Analyst Isolates Server:**
1. Update phase → CONTAINMENT
2. Note: "Server isolated, spread prevented"

**After Removing Malware:**
1. Update phase → ERADICATION
2. Note: "Malware removed, patches installed"

**After Testing System:**
1. Update phase → RECOVERY
2. Note: "System tested, restored to production"

**After Review:**
1. Update phase → CLOSED
2. Final note: "Root cause was phishing email, IT added email filter, user training complete"

---

## 🎯 How to Use Alerts & Incidents

### Daily Workflow (5 minutes)

1. **Check Alert List:**
   - Filter STATUS = "NEW"
   - Are there any unacknowledged alerts?
   - If yes, acknowledge and assign

2. **Check Incident List:**
   - Which incidents are still open?
   - Are they progressing through phases?
   - Any stuck for too long?

3. **Follow Up:**
   - Email analysts: "Status update?"
   - Ensure progress is being made

### When Critical Alert Arrives

**0 minutes:** Alert fires (RED, CRITICAL)

**1 minute:** You see it
- Click alert, read details
- Call analyst: "Critical alert just came in"

**2 minutes:** Acknowledge alert
- Click [ACK]
- Assign to best analyst

**3 minutes:** Analyst starts investigating
- Opens related incident
- Documents findings

**Next 2-24 hours:** Incident moves through phases
- DETECTION → ANALYSIS → CONTAINMENT → ERADICATION → RECOVERY → CLOSED

### For Defense Day

1. **Show Alert List** → "Here's all security alerts we tracked"
2. **Show Incident #7** → "Here's how we handled this attack"
3. **Walk through phases** → "NIST incident lifecycle"
4. **Show timeline** → "Actions taken, when, by whom"
5. **Show closed incident** → "Successfully resolved attack"

---

---

# 6. REPORTS MODULE

## 📄 What Is This Module?

**Simple:** Generate PDF reports for compliance audits and executive summary.

**Technical:** ReportLab-based PDF generation with threat timeline, compliance breakdown.

---

## 📊 Page 1: Report List

### What You See

Table of previously generated reports:

```
REPORT TYPE        │ DATE       │ GENERATED BY │ THREATS │ COMPLIANCE │ ACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Risk Assessment    │ 06-16 14:00│ analyst1     │ 1,000   │ —          │ [Download]
Compliance Report  │ 06-16 13:00│ compliance   │ —       │ 74%        │ [Download]
Risk Assessment    │ 06-15 09:30│ analyst1     │ 950     │ —          │ [Download]
Compliance Report  │ 06-14 16:00│ compliance   │ —       │ 72%        │ [Download]
```

### Each Column Explained

**Report Type:**
- Risk Assessment = Threat analysis, vulnerability list, recommendations
- Compliance Report = Framework breakdown, control assessment results

**Date:** When was it generated? (06-16 14:00 = June 16, 2:00 PM)

**Generated By:** Who created it?

**Threats:** How many threats analyzed?

**Compliance:** Overall compliance percentage?

**Action:** [Download] = Click to download PDF

### What You Can Do

1. **Review past reports** → See historical trends
2. **Download report** → PDF for sending to stakeholders
3. **Print report** → For board meetings, audits
4. **Archive report** → Kept for audit trail

---

## 🎯 Page 2: Generate Risk Report

### What You See

```
┌────────────────────────────────────────┐
│ Generate Risk Report                    │
├────────────────────────────────────────┤
│                                          │
│ Report Title:                            │
│ [Security Risk Assessment - June 2026]   │
│                                          │
│ Include:                                 │
│ ☑ Threat Timeline (30 days)             │
│ ☑ Severity Distribution                 │
│ ☑ Top Threats                           │
│ ☑ Vulnerability Summary                 │
│ ☑ Risk Score History                    │
│ ☑ Recommendations                       │
│                                          │
│ [Generate Report] [Cancel]              │
│                                          │
└────────────────────────────────────────┘
```

### What's in Risk Report?

**1. Executive Summary**
```
This report documents detected cybersecurity threats against
your healthcare systems for the period of June 1-16, 2026.

Total Threats Detected: 1,000
Critical Severity: 180
Risk Score: 7.2/10 (HIGH RISK)

Key Findings:
- DOS attacks peaked June 15 (peak: 1,000+ events)
- 40 unpatched vulnerabilities
- 6 healthcare systems monitored
```

**2. Threat Timeline Chart**
- Line chart showing daily threat count
- Last 30 days
- Shows attack patterns

**3. Severity Distribution**
- Breakdown by severity (CRITICAL, HIGH, MEDIUM, LOW)
- How many threats in each category?

**4. Top Threats**
- List of most common attack types
- DOS attacks (380)
- Brute Force (220)
- Network Scans (190)
- Etc.

**5. Vulnerability Summary**
- Count of open vulnerabilities
- CVSS scores
- Affected systems
- Patches available

**6. Risk Score Trend**
- How has risk score changed?
- Improving or worsening?

**7. Recommendations**
- "Patch these vulnerabilities"
- "Increase monitoring during peak attack hours (10-2 PM)"
- "Implement network segmentation"
- "Update security training"

### How to Generate

1. Click [Generate Risk Report]
2. Customize title if needed
3. Check boxes for sections to include
4. Click [Generate]
5. Wait 30 seconds (PDF being created)
6. Download PDF when ready

### When to Use

- **Monthly:** Generate for executive dashboard
- **Audit prep:** Show to auditor 2 weeks before audit
- **Board meeting:** Present threats and risk score
- **Stakeholder update:** Email to hospital leadership

---

## ✅ Page 3: Generate Compliance Report

### What You See

```
┌─────────────────────────────────────────┐
│ Generate Compliance Report               │
├─────────────────────────────────────────┤
│                                           │
│ Report Title:                             │
│ [Compliance Assessment - June 2026]       │
│                                           │
│ Include Frameworks:                       │
│ ☑ HIPAA (92% compliant)                  │
│ ☑ NDPR (60% compliant)                   │
│ ☑ ISO 27001 (70% compliant)              │
│                                           │
│ Include Details:                          │
│ ☑ Control Status Summary                 │
│ ☑ Failing Controls List                  │
│ ☑ Evidence Uploads                       │
│ ☑ Remediation Timeline                   │
│ ☑ Auditor Checklist                      │
│                                           │
│ [Generate Report] [Cancel]                │
│                                           │
└─────────────────────────────────────────┘
```

### What's in Compliance Report?

**1. Executive Summary**
```
Overall Compliance Score: 74%
Target Score: 80%
Gap: 6 additional controls needed

Frameworks Assessed:
- HIPAA: 92% (46/50 controls COMPLIANT)
- NDPR: 60% (18/30 controls COMPLIANT)
- ISO 27001: 70% (35/50 controls COMPLIANT)
```

**2. Framework Breakdown**

For each framework:
- Total controls
- Compliant controls
- Non-compliant controls
- Percentage score

**3. Failing Controls**
```
NON-COMPLIANT CONTROLS (16 total):

1. HIPAA §164.312(b) - Audit & Accountability
   Status: NON-COMPLIANT
   Required: Immutable audit logs with tamper detection
   Current State: Basic logging, no tamper detection
   Fix Deadline: 07-15-2026

2. NDPR Article 28 - Data Subject Rights
   Status: NON-COMPLIANT
   Required: Procedures to honor data deletion requests
   Current State: No formal process
   Fix Deadline: 07-30-2026
```

**4. Evidence Status**
- Shows uploaded evidence for each control
- What's documented, what's missing

**5. Remediation Timeline**
- When will each failing control be fixed?
- Who's responsible?
- Deadline?

**6. Auditor Checklist**
- Printable checklist
- Points auditor will check
- Your current status on each

### How to Generate

1. Click [Generate Compliance Report]
2. Select frameworks (usually all checked)
3. Check boxes for details to include
4. Click [Generate]
5. Wait 1 minute (PDF being created)
6. Download PDF when ready

### When to Use

- **Audit prep:** 1 month before audit, identify gaps
- **Remediation tracking:** Monthly progress on failing controls
- **Board report:** Show compliance progress
- **Auditor submission:** Day before audit, show current status

### Real Example

**Scenario:** Compliance audit scheduled for July 15

**May 15 Action:**
1. Generate Compliance Report
2. See: 74% compliant, need 6 more controls
3. See: 16 controls non-compliant

**May-July Action:**
1. Fix failing controls one by one
2. Upload evidence
3. Mark each as COMPLIANT

**July 14 Action:**
1. Generate final Compliance Report
2. Should show: 85% compliant (above 80% target)
3. Print and hand to auditor

---

## 🎯 How to Use Reports Module

### Monthly Workflow

1. **Generate Risk Report** → See threat trends
2. **Generate Compliance Report** → Track compliance progress
3. **Review both** → Any concerning trends?
4. **Share with leadership** → Email executive summary

### Audit Preparation (8 weeks before)

- **Week 1:** Generate Compliance Report → Identify gaps
- **Weeks 2-7:** Fix failing controls
- **Week 8:** Generate final report → Should be 80%+ compliant

### For Defense Day

1. **Show Risk Report:** "Here's threat landscape"
2. **Show Compliance Report:** "Here's our compliance status"
3. **Show charts:** "Threats over time"
4. **Explain gaps:** "Working on these 6 controls"
5. **Timeline:** "Will be 85% by month-end"

---

---

# 7. AUDIT LOG

## 📝 What Is This Module?

**Simple:** Record of every action anyone takes (read-only, can't be deleted).

**Technical:** Immutable append-only audit trail with SHA256 tamper detection.

---

## 📖 What You See

Table of all user actions:

```
TIMESTAMP      │ USER              │ ACTION                    │ RESOURCE    │ STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
06-16 14:32    │ analyst1          │ CREATE                    │ Alert #42   │ ✓
06-16 14:25    │ analyst1          │ UPDATE                    │ Incident #7 │ ✓
06-16 14:15    │ compliance        │ MARK_COMPLIANT            │ Control #5  │ ✓
06-16 13:50    │ admin             │ CREATE_USER               │ User #12    │ ✓
06-16 13:00    │ analyst2          │ DOWNLOAD                  │ Report #3   │ ✓
06-16 12:45    │ analyst1          │ UPDATE_INCIDENT           │ Incident #6 │ ✓
```

### Each Column Explained

**Timestamp:** When did this happen?
- Down to the minute (06-16 14:32 = June 16, 2:32 PM)

**User:** Who did it?
- analyst1, analyst2, compliance, admin

**Action:** What did they do?
- CREATE = Created something new
- UPDATE = Modified something
- DELETE = Removed something
- VIEW = Looked at something (read-only)
- DOWNLOAD = Downloaded a report
- ACKNOWLEDGE = Marked alert as acknowledged
- MARK_COMPLIANT = Marked control as compliant
- CREATE_USER = Created new user account

**Resource:** What were they acting on?
- Alert #42, Incident #7, Control #5, User #12, Report #3

**Status:** Did the action succeed?
- ✓ = Yes, succeeded
- ✗ = No, failed (error)

### Why This Matters

**Compliance Requirement:**
- HIPAA §164.312(b) = Must have audit trail
- NDPR Article 28 = Must track data access
- ISO 27001 A.12.4.1 = Event logging required

**Security Benefit:**
- Proves who accessed what and when
- Shows you didn't leak data (logs are tamper-proof)
- Helps detect insider threats

**Example Defense:**
- Regulator asks: "Did anyone unauthorized access patient data?"
- You show audit log: "Only nurses and doctors accessed patient data, at normal times, for legitimate chart reviews"
- Proves compliance ✓

### How to Use

1. **Search audit log** → Find specific user action
2. **Filter by date** → See actions on specific day
3. **Filter by user** → See what analyst1 has done
4. **Filter by action** → See all "MARK_COMPLIANT" actions
5. **Review suspicious patterns** → Did someone create 100 users?

### Real Example

**Scenario:** Patient complains data was accessed without permission

**What You Do:**
1. Go to Audit Log
2. Search for patient ID: "Record #2341"
3. See all access:
   - 06-16 10:15: Dr. Smith viewed chart (legitimate)
   - 06-16 11:00: Nurse Jones viewed chart (legitimate)
   - 06-16 14:32: Billing clerk accessed record (NOT legitimate)
4. Found the issue: Billing clerk shouldn't have accessed this chart
5. Show log to management: "See here, unauthorized access logged"
6. Action: Retrain billing clerk, tighten access controls

### Why It Can't Be Deleted

**Because:** Audit logs are append-only (can only add, never modify/delete)

**Why It's Important:**
- If someone could delete logs, they'd cover up crimes
- Immutable logs are evidence in court
- Regulators require logs that can't be tampered with

**How It Works:**
- Each log entry has SHA256 hash of previous entry
- If someone tries to delete/modify an entry, the hash breaks
- You can immediately see tampering occurred

---

## 🎯 How to Use Audit Log

### When Investigating Incident

1. Go to Audit Log
2. Filter by relevant data (patient ID, user, date range)
3. Review all actions
4. Look for suspicious patterns
5. Document findings

### Compliance Audit

1. Auditor asks: "Who accessed patient data last month?"
2. You pull Audit Log for last month
3. Show all access events with user, time, resource
4. Auditor confirms: "Good, only authorized staff accessed data"
5. Compliance verified ✓

### For Defense Day

- Show Audit Log
- Explain immutable design
- Show example: "Every action is logged and protected"
- Show audit trail for a specific incident

---

---

# 8. USER PROFILE

## 👤 What Is This Page?

**Simple:** Your personal account settings, password, security options.

**Technical:** User profile, password management, 2FA setup.

---

## 📋 What You See

### Account Information Section

```
┌─────────────────────────────────────────┐
│ Account Information                      │
├─────────────────────────────────────────┤
│                                          │
│ Email: analyst1@healthsec.local          │
│ Department: Security Operations          │
│ Phone: +234 (905) 123-4567               │
│ Member Since: May 15, 2026               │
│ Last Login: Today at 14:32               │
│ Last Login IP: 192.168.1.50              │
│                                          │
└─────────────────────────────────────────┘
```

**Email:** Your login email address

**Department:** Which part of hospital?
- Security Operations, Compliance, IT, etc.

**Phone:** Your contact number

**Member Since:** When account was created

**Last Login:** When you last logged in

**Last Login IP:** From which IP address?
- If different than normal, might be security concern

---

### Account Security Section

```
┌─────────────────────────────────────────┐
│ Account Security                        │
├─────────────────────────────────────────┤
│                                          │
│ Two-Factor Authentication (2FA):        │
│ ☐ Disabled                              │
│                                          │
│ Password Status:                         │
│ ✓ Current (changed 30 days ago)         │
│                                          │
│ [Change Password]                        │
│ [Setup 2FA]                              │
│                                          │
└─────────────────────────────────────────┘
```

**Two-Factor Authentication (2FA):**
- ☐ Disabled = Only need password
- ✓ Enabled = Need password + phone code
- Recommended: Enable for ANALYST+ roles

**Password Status:**
- ✓ Current = Changed recently (good)
- ⚠️ Old = Haven't changed in 90+ days (should update)
- 🔴 Change Required = Must change before next login

**Buttons:**
- [Change Password] = Update your password
- [Setup 2FA] = Add two-factor authentication

---

## 🎯 How to Use Profile

### Change Password

1. Click [Change Password]
2. Enter current password
3. Enter new password (minimum 12 characters, mix of uppercase/lowercase/numbers)
4. Confirm new password
5. Click [Save]

**When to Change:**
- Every 90 days (compliance requirement)
- If you suspect compromise
- If password was shared

### Setup 2FA

1. Click [Setup 2FA]
2. Scan QR code with phone authenticator app (Google Authenticator, Microsoft Authenticator)
3. Enter 6-digit code from app
4. Confirm setup
5. Save backup codes (in case phone lost)

**When Enabled:**
- Login requires password + 6-digit code from phone
- More secure, prevents account takeover
- Slightly slower login (extra 30 seconds)

### Review Account Details

- Check email address is correct
- Check department is accurate
- Check phone number current
- Review last login (did you login at that time?)
- Review last login IP (from your normal location?)

### For Defense Day

- Explain password policy: "Minimum 12 characters, complex, changed every 90 days"
- Show 2FA setup: "Optional but recommended for sensitive accounts"
- Explain audit trail: "Every login is logged with IP address"

---

---

# 9. ADMIN PANEL

## 🔧 What Is This Page?

**Simple:** System configuration for administrators only.

**Technical:** Django admin interface for managing users, systems, controls.

---

## 🚫 Who Can Access?

Only ADMIN role users can access `/admin/`

**Roles:**
- ADMIN = Full access (can do anything)
- COMPLIANCE = Can view and create assessments
- ANALYST = Can view and acknowledge alerts
- VIEWER = Read-only

---

## ⚙️ Main Admin Functions

### 1. User Management

**What You Can Do:**
- Create new user accounts
- Edit user roles (change VIEWER → ANALYST)
- Reset passwords
- Deactivate accounts
- View all users

**How:**
1. Go to `/admin/accounts/user/`
2. Click [Add User]
3. Enter: username, email, password
4. Set role: VIEWER, ANALYST, COMPLIANCE, ADMIN
5. Save

**Why:** Only admin can create accounts, assign roles

### 2. Healthcare Systems

**What You Can Do:**
- Create new healthcare systems to monitor
- Edit system details
- Mark as ACTIVE/INACTIVE
- Flag if contains PHI

**How:**
1. Go to `/admin/monitoring/healthcaresystem/`
2. Click [Add Healthcare System]
3. Enter: name, type, status, contains_phi flag
4. Save

**Why:** Define what you're monitoring

### 3. Compliance Frameworks

**What You Can Do:**
- Create frameworks (HIPAA, NDPR, ISO 27001)
- Add controls under each framework
- Set compliance requirements

**How:**
1. Go to `/admin/compliance/complianceframework/`
2. Click [Add Framework]
3. Enter: name (HIPAA), description, short_name
4. Save
5. Go to `/admin/compliance/control/`
6. Add controls under that framework

**Why:** Define what regulations you follow

### 4. Audit Log (View Only)

**What You Can See:**
- All audit log entries
- User actions, timestamps, resources

**What You CAN'T Do:**
- Modify entries (intentionally)
- Delete entries
- Change entries

**Why:** Audit logs must be immutable for compliance

---

## ⚠️ Important Notes for Admin

### Only Admin Can:
- Create/delete users
- Assign roles
- Create healthcare systems
- Create compliance frameworks
- Access `/admin/` panel

### Never Do:
- Delete audit logs (impossible anyway, immutable)
- Modify alert history
- Create fake incidents
- Change user roles without documentation

### Audit Trail:
- Every admin action is logged
- Auditors will check what admin did
- Document why you created user, changed role, etc.

---

## 🎯 Admin Workflow

### Daily (2 minutes)
- Check if new users need accounts
- No other daily tasks

### Weekly (10 minutes)
- Review admin actions in Audit Log
- Check if any users need deactivated
- Verify healthcare systems still accurate

### When New System Added
1. Create in Admin Panel
2. Assign data assets
3. Set up monitoring
4. Verify in Dashboard

### When New User Onboards
1. Create user account
2. Set role based on job
3. Send login credentials securely
4. User logs in, sets own password
5. Audit log shows account created

---

---

## 📚 SUMMARY: Quick Reference Table

| Page | What It Does | When to Use | Key Number |
|---|---|---|---|
| **Dashboard** | See all KPIs at a glance | Every login (30 sec) | Risk Score: 7.2/10 |
| **Monitoring** | Track who accesses data | Daily (5 min) | 159 suspicious activities |
| **Risk Engine** | Assess threat landscape | Weekly (10 min) | 1,000 threats |
| **Compliance** | Track regulations | Monthly (20 min) | 74% compliant |
| **Alerts** | Manage security warnings | As needed (urgent) | 46 critical alerts |
| **Reports** | Generate PDFs | Monthly/audit prep | 2 reports/month |
| **Audit Log** | View action history | Investigations | 100% immutable |
| **Profile** | Manage your account | Every 90 days | Change password |
| **Admin** | System configuration | Onboarding/new systems | ADMIN only |

---

## 🎓 For Defense Day Presentation

### Script (5 minutes)

"Good morning. I'm going to show you HealthSec, a healthcare cybersecurity and compliance monitoring system.

**First, the Dashboard** — This is where we monitor our security posture. We're currently at a 7.2/10 risk score, which is HIGH. This is composed of three factors: we have 1,000 detected threats, 40 open vulnerabilities, and 6 healthcare systems containing patient data.

We can see our threat timeline here — peaked on June 15 with over 1,000 threats. We also track compliance across three frameworks: HIPAA at 92%, NDPR at 60%, ISO 27001 at 70%, giving us an overall score of 74%.

**Moving to Monitoring** — We track all access to our healthcare systems. We have 159 suspicious activities flagged this week. For example, here's someone accessing the EHR at 3 AM from an unusual location — automatically flagged as suspicious.

**Risk Engine** — Shows all detected cybersecurity threats. We're using real NSL-KDD data from the University of New Brunswick — 1,000 actual network attacks. Our risk score algorithm combines threats, vulnerabilities, and PHI assets into a single 0-10 metric.

**Compliance Module** — We're tracking HIPAA, NDPR, and ISO 27001. For controls that we're failing, we upload evidence and remediate. Currently at 74% overall compliance, targeting 80% by month-end.

**Alerts & Incidents** — We have 46 critical alerts requiring action. When an alert fires, we create an incident and track it through NIST lifecycle: Detection, Analysis, Containment, Eradication, Recovery, and Closed. Here's an example incident that we handled in 3 days.

**Reports** — We generate compliance and risk reports monthly. These are PDF documents suitable for auditors and board presentations.

**Audit Log** — Every action is recorded in an immutable, tamper-proof audit trail. This shows full accountability for who accessed what data and when.

Finally, this system is fully deployed on GitHub and ready for production use. Any questions?"

---

**END OF HOW_TO_USE GUIDE**

*Suitable for supervisors, defense day presentations, and self-learning.*  
*Last updated: June 2026*
