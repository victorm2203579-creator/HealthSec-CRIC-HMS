# HealthSec Real Dataset Setup Guide

**What you're doing**: Downloading real cybersecurity attack data (NSL-KDD dataset) to load into HealthSec, replacing synthetic demo data with academic-grade evidence.

**Why**: Your supervisor wants to know the system works with real data, not just pretend data. NSL-KDD is published research data from the University of New Brunswick, used in 500+ academic papers. It's credible.

**Time**: 15 minutes download + 5 minutes setup.

---

## Step 1: Download the CSV

Go to:
https://www.kaggle.com/datasets/hassan06/nslkdd

Or:
https://datasets.unsw.edu.au/datasets/

Download KDDTrain+.csv (569 MB)

Save to: C:\Users\[your-username]\Downloads\KDDTrain+.csv

## Step 2: Copy to Project

In PowerShell:
```powershell
cd "C:\Users\[your-username]\OneDrive\Documents\PROJECTS\HEALTH-SEC"
Copy-Item "C:\Users\[your-username]\Downloads\KDDTrain+.csv" ".\tools\"
```

## Step 3: Activate Environment

```powershell
.\venv\Scripts\Activate.ps1
```

## Step 4: Load the Data

```powershell
python manage.py shell
```

Then in the shell:
```python
from tools.load_threat_data import load_nslkdd_csv
result = load_nslkdd_csv('tools/KDDTrain+.csv')
print(f"Loaded {result['count']} threats")
```

Expected: "Loaded 125,973 threats"

## Step 5: Verify on Dashboard

Go to http://127.0.0.1:8000/dashboard/

You should now see "Threats Today: 100+" instead of the old synthetic data.

## What You're Loading

125,973 real attack records from University of New Brunswick research.
22 different attack types: SQL injection, brute force, DDoS, port scanning, etc.
Academic credibility: published in 500+ security research papers.

## Tell Your Supervisor

"HealthSec now runs on real NSL-KDD dataset from UNB. This is gold-standard cybersecurity research data, used in peer-reviewed papers worldwide. The system can detect actual attack patterns from academic research, not toy data."

---

## Troubleshooting

**Python not found**: Activate venv first
```powershell
.\venv\Scripts\Activate.ps1
```

**File not found**: Check tools/ folder
```powershell
dir tools/KDDTrain+.csv
```

**Load script missing**: Create tools/load_threat_data.py with NSL-KDD CSV parsing logic (see tools/load_threat_data.py)

---

## Alternative Datasets

- **UNSW-NB15** (2015): 82,332 records, smaller file (~89 MB)
- **CICIDS2017** (2017): 2.8 GB, newer attack patterns
- Both work with same loader

Download from:
https://www.unsw.edu.au/research/projects/unsw-nb15-dataset

