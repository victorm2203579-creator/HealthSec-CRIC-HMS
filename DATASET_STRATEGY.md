# HealthSec CRIC HMS — Dataset Strategy

## Overview
Combine **real cybersecurity datasets** with **simulated healthcare data** to create a production-grade, academically credible system.

---

## Part A: Real Cybersecurity Datasets

### 1. **CICIDS2017** (Best for IDS/Network Anomaly Detection)
- **URL**: https://www.unb.ca/cic/datasets/ids-2017.html
- **Size**: ~2.8 GB (CSV format)
- **What it contains**:
  - 80 network flow features
  - Labeled attacks: DoS, DDoS, Brute Force, Port Scan, Web Attack, Botnet, Infiltration
  - Captures legitimate and malicious traffic
- **Use in HealthSec**:
  - Feed threat events and vulnerabilities
  - Create risk scoring baselines
  - Train ML anomaly detector
  - Populate threat intelligence feed

### 2. **UNSW-NB15** (Cybersecurity Intrusions Dataset)
- **URL**: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity-datasets/
- **Size**: ~1.4 GB (CSV, raw PCAP)
- **What it contains**:
  - 49 flow/packet features
  - Modern attack types: Fuzzers, Reconnaissance, Backdoors, DoS, Exploits, Shellcode, Worms
  - Better balanced for ML training
- **Use in HealthSec**:
  - Supplement CICIDS2017 for diversity
  - Create vulnerability records with real CVSS scores
  - Build threat actor profiles

### 3. **Kaggle Security Datasets** (Quick Start)
Popular options for rapid prototyping:
- **Cyber Threat Intelligence**: https://www.kaggle.com/datasets
- **Intrusion Detection**: Multiple curated datasets
- **Download**: Use Kaggle API or browser

---

## Part B: Simulated Healthcare Data

Create realistic **PHI (Protected Health Information)** that doesn't violate HIPAA:

### 1. **Patient Records** (Synthetic - Use Faker Library)
```python
# tools/generate_healthcare_data.py
from faker import Faker
from monitoring.models import PatientRecord

fake = Faker()

for i in range(500):
    PatientRecord.objects.create(
        patient_code=f'PAT-{i:06d}',
        record_type=choice(['MEDICAL_HISTORY', 'LAB_RESULT', 'PRESCRIPTION']),
        sensitivity_level=choice(['LOW', 'MEDIUM', 'CRITICAL']),
        department=choice(['Cardiology', 'Oncology', 'ICU', 'ER']),
        created_by=request.user,
    )
```

### 2. **Access Logs** (Synthetic - Random Patterns)
```python
# tools/generate_access_logs.py
for i in range(10000):
    RecordAccessLog.objects.create(
        user=random_user,
        patient_record=random_patient,
        access_type=choice(['VIEW', 'DOWNLOAD', 'PRINT']),
        access_hour=random.randint(0, 23),
        device_info=fake.user_agent(),
        ip_address=fake.ipv4(),
    )
```

### 3. **Suspicious Activity** (Rule-Based + Synthetic)
Combine detection rules:
- After-hours access (22:00–06:00)
- Bulk access (15+ records in 1 hour)
- Cross-department access
- Download/Print sensitive records
- New device fingerprints

---

## Integration Strategy

### **Phase 1: Load Real Cybersecurity Data**
1. Download CICIDS2017 or UNSW-NB15
2. Parse CSV → Extract network flows, protocols, attacks
3. Create `ThreatEvent` records with real attack labels
4. Create `VulnerabilityRecord` from known CVEs (use NVD API)
5. Populate `RiskScore` based on real threat indicators

### **Phase 2: Generate Synthetic Healthcare**
1. Create 500–1000 synthetic patient records
2. Generate 10,000–50,000 access logs with realistic patterns
3. Inject anomalies:
   - 5% suspicious access events
   - 10% cross-department access
   - 2% after-hours downloads
4. Run monitoring engine to flag suspicious activity

### **Phase 3: Integrate for Demo**
1. Correlate cybersecurity threats with healthcare systems
2. Create compliance gaps based on threat severity
3. Generate risk assessments that reference real attack types
4. Show audit trail of synthetic but plausible incidents

---

## Tools & Scripts

### **Download CICIDS2017**
```bash
# Register at UNB, then download via browser or:
wget https://www.unb.ca/cic/datasets/ids-2017/ids-2017.zip
unzip ids-2017.zip
# Files: Monday-Friday CSV files
```

### **Parse into Django Models**
Create **tools/load_threat_data.py**:
```python
import pandas as pd
from risk_engine.models import ThreatEvent, VulnerabilityRecord

df = pd.read_csv('Monday-WorkingHours.pcap_ISCX.csv')

# Map columns
for _, row in df.iterrows():
    if row['Label'] != 'BENIGN':
        ThreatEvent.objects.create(
            title=f"{row['Label']} detected",
            description=f"Source: {row.get('Src IP', 'unknown')}",
            severity=threat_to_severity(row['Label']),
            classification='EXTERNAL',
            occurred_at=timezone.now(),
        )

# Run: python manage.py shell < tools/load_threat_data.py
```

### **Generate Synthetic Healthcare**
Create **tools/generate_demo_data.py**:
```python
from faker import Faker
from monitoring.models import PatientRecord, RecordAccessLog
from django.contrib.auth import get_user_model
import random

fake = Faker()
User = get_user_model()

# Create patients
for i in range(500):
    PatientRecord.objects.create(
        patient_code=f'PAT-{i:06d}',
        record_type=random.choice(['MEDICAL_HISTORY', 'LAB_RESULT', 'PRESCRIPTION']),
        sensitivity_level=random.choice(['LOW', 'MEDIUM', 'CRITICAL']),
        department=random.choice(['Cardiology', 'Oncology', 'ICU', 'ER']),
        created_by=User.objects.first(),
    )

# Create access logs with anomalies
users = list(User.objects.filter(is_active=True))
patients = list(PatientRecord.objects.all())

for i in range(10000):
    # 95% normal, 5% suspicious
    user = random.choice(users)
    patient = random.choice(patients)
    
    if random.random() < 0.05:
        # Suspicious pattern
        hour = random.choice([2, 3, 22, 23])  # After-hours
        access_type = 'DOWNLOAD'
    else:
        # Normal pattern
        hour = random.randint(8, 17)
        access_type = random.choice(['VIEW', 'VIEW', 'VIEW', 'DOWNLOAD'])
    
    RecordAccessLog.objects.create(
        user=user,
        patient_record=patient,
        access_type=access_type,
        access_hour=hour,
        device_info=fake.user_agent(),
        ip_address=fake.ipv4(),
    )

print("✅ Demo data generated successfully")

# Run: python manage.py shell < tools/generate_demo_data.py
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Real Cybersecurity Datasets (CICIDS2017 / UNSW-NB15)       │
│  ↓                                                           │
│  Parse Network Flows → Extract Attacks → CVE Lookups       │
│  ↓                                                           │
│  ThreatEvent, VulnerabilityRecord, ThreatIntelFeed         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  HealthSec Risk Scoring Engine                              │
│  • Aggregates threat data                                   │
│  • Calculates risk scores (0–10)                            │
│  • Creates RiskScore records                                │
│  • Flags vulnerabilities by CVSS                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Synthetic Healthcare Data                                  │
│  • PatientRecord (500–1000 records)                         │
│  • RecordAccessLog (10,000–50,000 entries)                  │
│  • Inject 5% suspicious activity                            │
│  • Correlate with threat landscape                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Monitoring & Detection Engine                              │
│  • Flag suspicious access patterns                          │
│  • Correlate with threat intelligence                       │
│  • Generate alerts & incidents                              │
│  • Compliance gap analysis                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start Commands

```bash
# 1. Download datasets
cd /tmp
wget https://www.unb.ca/cic/datasets/ids-2017/ids-2017.zip
unzip ids-2017.zip

# 2. Copy to project
mkdir -p datasets
cp ids-2017/*.csv datasets/

# 3. Load threat data
python manage.py shell < tools/load_threat_data.py

# 4. Generate healthcare data
python manage.py shell < tools/generate_demo_data.py

# 5. Run risk assessment
python manage.py shell
>>> from risk_engine.services import RiskScoringService
>>> service = RiskScoringService()
>>> result = service.compute()

# 6. Verify data loaded
python manage.py shell
>>> from risk_engine.models import ThreatEvent, VulnerabilityRecord
>>> ThreatEvent.objects.count()  # Should be 100s
>>> VulnerabilityRecord.objects.count()  # Should be 100s
```

---

## Academic Credibility

✅ **Real Data**: CICIDS2017/UNSW-NB15 are peer-reviewed, published datasets
✅ **Realistic Scenarios**: Healthcare context is simulated but plausible
✅ **Compliance Ready**: HIPAA-compatible (no real PHI, synthetic identifiers)
✅ **Reproducible**: Open-source datasets, documented generation process
✅ **Scalable**: Easy to extend with more datasets or real threat feeds

---

## Next Steps

1. **Download CICIDS2017** (or UNSW-NB15)
2. **Create `tools/` directory** with data loading scripts
3. **Load data** into HealthSec models
4. **Run risk assessment** to verify integration
5. **Test UI** with real threat data + synthetic healthcare
6. **Document** in project README

---

**This approach gives you:**
- ✅ Real cybersecurity intelligence (credible for academic/demo use)
- ✅ Synthetic healthcare that protects privacy
- ✅ Production-ready data pipeline
- ✅ Reproducible, shareable methodology
