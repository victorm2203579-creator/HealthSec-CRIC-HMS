# ML Anomaly Detection Implementation — HealthSec CRIC HMS

## Overview

Complete machine learning-based anomaly detection system using Isolation Forest algorithm to detect statistical deviations from normal user access patterns in healthcare information systems.

---

## Implementation Summary

### Core Files

1. **risk_engine/ml_detector.py** (400+ lines)
   - `extract_features(record_access_log)` — Extracts 11 behavioral features
   - `AnomalyDetector` class with methods:
     - `train()` — Train model on historical access logs (last 1000)
     - `predict(record_access_log)` — Predict anomaly with confidence score
     - `batch_analyze(days=7)` — Scan and flag anomalies in time period
     - `get_model_status()` — Return training status and metadata
     - `load_model()` — Load from disk persistence
   - Model saved to: `media/models/anomaly_detector.pkl`
   - Scaler saved to: `media/models/anomaly_scaler.pkl`
   - Metadata saved to: `media/models/anomaly_metadata.json`

2. **risk_engine/management/commands/train_anomaly_model.py**
   ```bash
   python manage.py train_anomaly_model [--verbose]
   ```
   - Trains Isolation Forest on recent access logs
   - Displays training results and statistics
   - Saves model and metadata for future predictions

3. **risk_engine/management/commands/run_anomaly_scan.py**
   ```bash
   python manage.py run_anomaly_scan [--days 7] [--verbose]
   ```
   - Scans recent access logs for anomalies
   - Creates SuspiciousActivity records for flagged accesses
   - Displays analyzed count and anomalies found

4. **risk_engine/views.py** (added ml_model_status view)
   - Displays model training status
   - Shows feature documentation
   - Provides control panel for training and scanning

5. **risk_engine/urls.py** (added ml-status route)
   - URL: `/risk/ml-status/`
   - View: `ml_model_status`

6. **risk_engine/templates/risk_engine/ml_status.html**
   - Dark-themed status dashboard
   - Model status card with training info
   - 11-feature documentation table
   - Control panel with Train/Scan buttons
   - Algorithm explanation

7. **monitoring/engine.py** (integrated ML predictions)
   - Added `'ml_anomaly': 35` to SCORE_WEIGHTS
   - Added `_is_ml_anomaly(access_log)` method
   - Updated `analyze_access()` to call ML check
   - Updated flag descriptions and activity types

---

## Features Analyzed (11 Behavioral Indicators)

| # | Feature | Description | Type |
|---|---------|-------------|------|
| 1 | access_hour | Hour of day (0-23) | Time |
| 2 | access_day_of_week | Day of week (0=Mon, 6=Sun) | Time |
| 3 | is_weekend | Weekend flag (0 or 1) | Time |
| 4 | records_accessed_last_hour | Access count (past hour) | Volume |
| 5 | records_accessed_today | Access count (today) | Volume |
| 6 | is_after_hours | After-hours flag (before 7am or after 8pm) | Risk |
| 7 | is_cross_department | Cross-department access flag | Risk |
| 8 | sensitivity_level_encoded | Record sensitivity (0=LOW, 1=MED, 2=HIGH, 3=CRIT) | Data Class |
| 9 | access_type_encoded | Access action (0=VIEW, 1=EDIT, 2=DOWNLOAD, 3=PRINT, 4=DELETE) | Data Class |
| 10 | user_avg_daily_accesses | User's average (past 30 days) | Baseline |
| 11 | deviation_from_avg | Standardized deviation from baseline | Baseline |

---

## Usage Guide

### 1. Train the Model

```bash
cd c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC
python manage.py train_anomaly_model --verbose
```

**Output:**
```
[OK] Model trained successfully
  Trained on 1000 records
  Trained at 2026-05-25T10:30:45.123Z
  
Model Configuration:
  Algorithm: Isolation Forest
  Contamination rate: 0.1 (10%)
  Features: 11
  ...
```

### 2. Run Anomaly Scan

```bash
python manage.py run_anomaly_scan --days 7 --verbose
```

**Output:**
```
[RESULTS]
  Analyzed: 500 access logs
  Anomalies: 12 detected
  
[ALERT] 12 suspicious activities created
Review them in the admin panel or use the monitoring dashboard.

Anomaly rate: 2.40%
```

### 3. View Model Status

Navigate to: `http://localhost:8000/risk/ml-status/`

Features:
- Real-time model training status
- Feature documentation table
- Train Model button
- Run Anomaly Scan button (if model trained)
- Explanation of Isolation Forest algorithm

---

## Integration with Monitoring Engine

When analyzing access logs, the monitoring engine now:

1. **Runs rule-based checks** (after_hours, bulk_access, cross_department, etc.)
2. **Runs ML prediction** via `_is_ml_anomaly()` method
3. **Combines results** using weighted scoring:
   - ML anomaly flag: 35 points (high weight)
   - Other flags: 15-30 points each
4. **Creates alerts** if total score ≥ 40 (SUSPICION_THRESHOLD)

Example flow:
```python
access_log = RecordAccessLog(...)
engine = MonitoringEngine()
score, flags = engine.analyze_access(access_log)
# Returns: (score=70, flags=['after_hours', 'ml_anomaly', 'cross_department'])
```

---

## HIPAA Compliance

✓ **No PHI in predictions** — Uses opaque user/record IDs only
✓ **Graceful degradation** — Continues with rules if ML unavailable
✓ **Audit logging** — All detections logged to AuditLog
✓ **Confidence threshold** — Only flags anomalies >50% confidence

---

## Technical Details

### Algorithm: Isolation Forest

- **Type**: Unsupervised anomaly detection
- **Contamination Rate**: 0.1 (expects ~10% anomalies)
- **Random State**: 42 (reproducible results)
- **Feature Scaling**: StandardScaler (z-score normalization)
- **Training Data**: Last 1,000 access logs
- **Confidence Score**: Based on anomaly depth (0-100%)

### Model Persistence

- **Format**: Pickle (joblib serialization)
- **Location**: `media/models/` directory
- **Files**:
  - `anomaly_detector.pkl` — Trained IsolationForest model
  - `anomaly_scaler.pkl` — StandardScaler for feature normalization
  - `anomaly_metadata.json` — Training metadata and status

### Error Handling

- Model training failures are logged but don't break the system
- Prediction errors are caught and return None (graceful fallback)
- ML check returns False if model not trained or available
- Monitoring engine continues with rule-based checks

---

## Testing Checklist

- [x] ML detector module imports successfully
- [x] AnomalyDetector instantiates without errors
- [x] Feature extraction works on RecordAccessLog instances
- [x] Model status retrieval works (trained/untrained)
- [x] Management commands are discoverable
- [x] URL routing resolves correctly
- [x] Integration with monitoring engine works
- [x] Django checks pass (0 issues for ML integration)
- [x] Template renders correctly
- [x] Graceful error handling in all components

---

## Next Steps (Optional)

1. **Train on production data** — Run training command with actual access logs
2. **Monitor detection results** — Check SuspiciousActivity records for anomalies
3. **Tune contamination rate** — Adjust from 0.1 if needed based on results
4. **Add model retraining schedule** — Run training weekly via cron/scheduler
5. **Email alerts for high-confidence anomalies** — Integrate with alert system
6. **Model performance metrics** — Track precision/recall over time

---

## Support Commands

```bash
# Get model training information
python manage.py shell
>>> from risk_engine.ml_detector import AnomalyDetector
>>> detector = AnomalyDetector()
>>> print(detector.get_model_status())

# Check anomaly scan results
>>> from monitoring.models import SuspiciousActivity
>>> anomalies = SuspiciousActivity.objects.filter(activity_type='UNUSUAL_VOLUME')
>>> print(f"Found {anomalies.count()} anomalies")

# View training metadata
>>> import json
>>> with open('media/models/anomaly_metadata.json') as f:
...     metadata = json.load(f)
...     print(json.dumps(metadata, indent=2))
```

---

## Files Created/Modified

### New Files
- `risk_engine/ml_detector.py` — Core ML module
- `risk_engine/management/commands/train_anomaly_model.py` — Training command
- `risk_engine/management/commands/run_anomaly_scan.py` — Scanning command
- `risk_engine/management/commands/__init__.py` — Package init
- `risk_engine/management/__init__.py` — Package init
- `risk_engine/templates/risk_engine/ml_status.html` — Status dashboard
- `ML_ANOMALY_DETECTION.md` — This documentation

### Modified Files
- `risk_engine/views.py` — Added ml_model_status view
- `risk_engine/urls.py` — Added ml-status URL route
- `monitoring/engine.py` — Integrated ML predictions into analyze_access()

---

**Implementation Status**: ✓ Complete and Tested
**Version**: 1.0
**Last Updated**: 2026-05-25
