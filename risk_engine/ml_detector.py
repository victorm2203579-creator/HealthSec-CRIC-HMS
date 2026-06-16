"""
risk_engine/ml_detector.py
==========================
Machine Learning-based Anomaly Detection for healthcare access monitoring.

Uses Isolation Forest (unsupervised learning) to detect statistical deviations
from normal user behavior patterns without requiring labeled attack data.

HIPAA Compliance:
- No PHI in model predictions or logs
- Uses opaque user/record IDs only
- All detections logged to AuditLog
- No model artifacts contain sensitive data
"""

import logging
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from monitoring.models import RecordAccessLog, SuspiciousActivity, PatientRecord
from audit.utils import log_event

logger = logging.getLogger(__name__)


def extract_features(record_access_log):
    """
    Extract ML features from a RecordAccessLog entry.

    Returns a list of 11 numeric features for the model:
    [access_hour, access_day_of_week, is_weekend, records_accessed_last_hour,
     records_accessed_today, is_after_hours, is_cross_department,
     sensitivity_level_encoded, access_type_encoded, user_avg_daily_accesses,
     deviation_from_avg]

    Args:
        record_access_log: RecordAccessLog instance

    Returns:
        list: 11 feature values (all numeric)
    """
    try:
        timestamp = record_access_log.timestamp
        user = record_access_log.user
        patient_record = record_access_log.patient_record

        # Feature 1: Access hour (0-23)
        access_hour = timestamp.hour

        # Feature 2: Day of week (0-6, where 0=Monday)
        access_day_of_week = timestamp.weekday()

        # Feature 3: Is weekend (0 or 1)
        is_weekend = 1 if access_day_of_week >= 5 else 0

        # Feature 4: Records accessed in last hour
        one_hour_ago = timestamp - timedelta(hours=1)
        records_accessed_last_hour = RecordAccessLog.objects.filter(
            user=user,
            timestamp__gte=one_hour_ago,
            timestamp__lte=timestamp
        ).count()

        # Feature 5: Records accessed today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        records_accessed_today = RecordAccessLog.objects.filter(
            user=user,
            timestamp__gte=today_start,
            timestamp__lte=timestamp
        ).count()

        # Feature 6: Is after hours (0 or 1: hour < 7 or > 20)
        is_after_hours = 1 if access_hour < 7 or access_hour > 20 else 0

        # Feature 7: Is cross-department access (0 or 1)
        user_dept = getattr(user, 'department', None)
        record_dept = patient_record.department
        is_cross_department = 1 if user_dept and user_dept != record_dept else 0

        # Feature 8: Sensitivity level encoded (0=LOW, 1=MEDIUM, 2=HIGH, 3=CRITICAL)
        sensitivity_encoding = {
            PatientRecord.SensitivityLevel.LOW: 0,
            PatientRecord.SensitivityLevel.MEDIUM: 1,
            PatientRecord.SensitivityLevel.HIGH: 2,
            PatientRecord.SensitivityLevel.CRITICAL: 3,
        }
        sensitivity_level_encoded = sensitivity_encoding.get(patient_record.sensitivity_level, 1)

        # Feature 9: Access type encoded (0=VIEW, 1=EDIT, 2=DOWNLOAD, 3=PRINT, 4=DELETE)
        access_type_encoding = {
            RecordAccessLog.AccessType.VIEW: 0,
            RecordAccessLog.AccessType.EDIT: 1,
            RecordAccessLog.AccessType.DOWNLOAD: 2,
            RecordAccessLog.AccessType.PRINT: 3,
            RecordAccessLog.AccessType.DELETE: 4,
        }
        access_type_encoded = access_type_encoding.get(record_access_log.access_type, 0)

        # Feature 10: User's average daily accesses (historical)
        thirty_days_ago = today_start - timedelta(days=30)
        daily_counts = RecordAccessLog.objects.filter(
            user=user,
            timestamp__gte=thirty_days_ago,
            timestamp__lte=today_start
        ).extra(
            select={'day': 'DATE(timestamp)'}
        ).values('day').annotate(count=Count('id'))

        if daily_counts.exists():
            total_accesses = sum(item['count'] for item in daily_counts)
            user_avg_daily_accesses = total_accesses / len(daily_counts)
        else:
            user_avg_daily_accesses = 0

        # Feature 11: Deviation from average (standardized)
        if user_avg_daily_accesses > 0:
            deviation_from_avg = (records_accessed_today - user_avg_daily_accesses) / user_avg_daily_accesses
        else:
            deviation_from_avg = 0

        return [
            access_hour,
            access_day_of_week,
            is_weekend,
            records_accessed_last_hour,
            records_accessed_today,
            is_after_hours,
            is_cross_department,
            sensitivity_level_encoded,
            access_type_encoded,
            user_avg_daily_accesses,
            deviation_from_avg,
        ]

    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        return None


class AnomalyDetector:
    """
    Isolation Forest-based anomaly detector for healthcare access patterns.

    Learns normal behavior from historical access logs and flags deviations.
    """

    def __init__(self):
        """Initialize the anomaly detector."""
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_dir = Path(settings.MEDIA_ROOT) / 'models'
        self.model_path = self.model_dir / 'anomaly_detector.pkl'
        self.scaler_path = self.model_dir / 'anomaly_scaler.pkl'
        self.metadata_path = self.model_dir / 'anomaly_metadata.json'

        # Create model directory if it doesn't exist
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def prepare_training_data(self):
        """
        Prepare training data from recent RecordAccessLog entries.

        Queries last 1000 access logs and extracts features from each.

        Returns:
            tuple: (numpy array of features, list of RecordAccessLog IDs)
        """
        try:
            # Get last 1000 access logs
            recent_logs = RecordAccessLog.objects.all().order_by('-timestamp')[:1000]

            if not recent_logs.exists():
                logger.warning("No access logs found for training")
                return None, []

            features_list = []
            log_ids = []

            for log in recent_logs:
                features = extract_features(log)
                if features is not None:
                    features_list.append(features)
                    log_ids.append(log.log_id)

            if not features_list:
                logger.warning("Could not extract features from any logs")
                return None, []

            return np.array(features_list), log_ids

        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
            return None, []

    def train(self):
        """
        Train the Isolation Forest model on historical access logs.

        Returns:
            dict: Training summary with counts and metadata
        """
        try:
            logger.info("Starting anomaly detector training...")

            # Prepare data
            X, log_ids = self.prepare_training_data()

            if X is None or len(X) == 0:
                logger.error("No training data available")
                return {
                    'success': False,
                    'message': 'No training data available',
                    'trained_records': 0,
                }

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled)
            self.is_trained = True

            # Save model and scaler
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)

            # Save metadata
            import json
            metadata = {
                'trained_at': timezone.now().isoformat(),
                'trained_records': len(X),
                'contamination_rate': 0.1,
                'algorithm': 'IsolationForest',
                'features': 11,
                'feature_names': [
                    'access_hour',
                    'access_day_of_week',
                    'is_weekend',
                    'records_accessed_last_hour',
                    'records_accessed_today',
                    'is_after_hours',
                    'is_cross_department',
                    'sensitivity_level_encoded',
                    'access_type_encoded',
                    'user_avg_daily_accesses',
                    'deviation_from_avg',
                ]
            }
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            log_event(
                action='ML_MODEL_TRAINED',
                description=f'Anomaly detector trained on {len(X)} access logs'
            )

            logger.info(f"Training completed. Trained on {len(X)} records.")

            return {
                'success': True,
                'message': 'Model trained successfully',
                'trained_records': len(X),
                'trained_at': metadata['trained_at'],
            }

        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            log_event(
                action='ML_MODEL_TRAIN_FAILED',
                description=f'Model training failed: {str(e)}'
            )
            return {
                'success': False,
                'message': f'Training failed: {str(e)}',
                'trained_records': 0,
            }

    def load_model(self):
        """
        Load trained model and scaler from disk.

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                logger.info("Model and scaler loaded successfully")
                return True
            else:
                logger.warning("Model or scaler file not found")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False

    def predict(self, record_access_log):
        """
        Predict if a RecordAccessLog entry is anomalous.

        Args:
            record_access_log: RecordAccessLog instance

        Returns:
            dict: Prediction result with anomaly flag, score, and confidence
        """
        try:
            # Ensure model is loaded
            if not self.is_trained:
                if not self.load_model():
                    logger.warning("Model not trained and could not be loaded")
                    return None

            # Extract features
            features = extract_features(record_access_log)
            if features is None:
                logger.error("Could not extract features")
                return None

            # Prepare for prediction
            X = np.array(features).reshape(1, -1)
            X_scaled = self.scaler.transform(X)

            # Predict
            prediction = self.model.predict(X_scaled)[0]
            anomaly_score = self.model.score_samples(X_scaled)[0]

            # Convert to interpretable format
            is_anomaly = prediction == -1

            # Confidence: more negative score = more anomalous
            # Normalize to 0-100 scale
            confidence = min(100, max(0, abs(anomaly_score) * 100))

            result = {
                'is_anomaly': is_anomaly,
                'anomaly_score': float(anomaly_score),
                'confidence': float(confidence),
                'features_used': {
                    'access_hour': features[0],
                    'access_day_of_week': features[1],
                    'is_weekend': features[2],
                    'records_accessed_last_hour': features[3],
                    'records_accessed_today': features[4],
                    'is_after_hours': features[5],
                    'is_cross_department': features[6],
                    'sensitivity_level_encoded': features[7],
                    'access_type_encoded': features[8],
                    'user_avg_daily_accesses': features[9],
                    'deviation_from_avg': features[10],
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error in prediction: {str(e)}")
            return None

    def batch_analyze(self, days=7):
        """
        Analyze all recent access logs and flag anomalies.

        Args:
            days: Number of days to look back

        Returns:
            dict: Summary of analysis with counts
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            recent_logs = RecordAccessLog.objects.filter(
                timestamp__gte=cutoff_date
            ).order_by('-timestamp')

            analyzed_count = 0
            anomalies_count = 0

            logger.info(f"Starting batch analysis of {recent_logs.count()} logs...")

            for log in recent_logs:
                # Skip if already marked as suspicious by rule engine
                if log.is_suspicious:
                    continue

                prediction = self.predict(log)
                if prediction is None:
                    continue

                analyzed_count += 1

                if prediction['is_anomaly']:
                    anomalies_count += 1

                    # Create SuspiciousActivity record
                    SuspiciousActivity.objects.create(
                        user=log.user,
                        activity_type=SuspiciousActivity.ActivityType.UNUSUAL_VOL,
                        description=(
                            f"ML anomaly detected: access confidence {prediction['confidence']:.1f}%, "
                            f"score {prediction['anomaly_score']:.3f}"
                        ),
                        severity=SuspiciousActivity.Severity.MEDIUM,
                        related_record=log.patient_record,
                    )

                    # Update the access log
                    log.is_suspicious = True
                    log.suspicion_reason = f"ML_ANOMALY (confidence: {prediction['confidence']:.1f}%)"
                    log.save()

            log_event(
                action='ML_BATCH_ANALYSIS',
                description=f'Analyzed {analyzed_count} logs, found {anomalies_count} anomalies'
            )

            logger.info(f"Batch analysis complete: {anomalies_count} anomalies found")

            return {
                'analyzed': analyzed_count,
                'anomalies_found': anomalies_count,
                'analysis_period_days': days,
            }

        except Exception as e:
            logger.error(f"Error in batch analysis: {str(e)}")
            return {
                'analyzed': 0,
                'anomalies_found': 0,
                'error': str(e),
            }

    def get_model_status(self):
        """
        Get current status of the trained model.

        Returns:
            dict: Model status information
        """
        try:
            import json

            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)

                return {
                    'is_trained': True,
                    'trained_at': metadata.get('trained_at'),
                    'trained_records': metadata.get('trained_records'),
                    'algorithm': metadata.get('algorithm'),
                    'feature_count': metadata.get('features'),
                }
            else:
                return {
                    'is_trained': False,
                    'trained_at': None,
                    'trained_records': 0,
                }
        except Exception as e:
            logger.error(f"Error getting model status: {str(e)}")
            return {
                'is_trained': False,
                'error': str(e),
            }
