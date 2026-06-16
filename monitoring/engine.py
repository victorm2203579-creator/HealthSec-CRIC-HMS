"""
monitoring/engine.py
====================
MonitoringEngine — analyses patient record access logs for suspicious
activity patterns and coordinates alert creation.

Usage:
    from monitoring.engine import MonitoringEngine

    engine = MonitoringEngine()
    score, flags = engine.analyze_access(access_log_instance)
    engine.flag_suspicious_activity(access_log_instance, score, flags)
"""

from datetime import timedelta

from django.utils import timezone

# Weight each risk flag contributes to the 0-100 suspicion score.
SCORE_WEIGHTS = {
    'after_hours': 25,
    'bulk_access': 30,
    'cross_department': 20,
    'critical_record': 15,
    'unknown_device': 25,
    'ml_anomaly': 35,  # ML-detected anomaly weight
}

# Threshold above which an access event is considered suspicious.
SUSPICION_THRESHOLD = 40


class MonitoringEngine:
    """
    Analyses RecordAccessLog entries for behavioural anomalies.

    Each method is self-contained and can be unit-tested independently.
    The public entry point is analyze_access(); call flag_suspicious_activity()
    afterwards to persist findings and raise alerts.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_access(self, access_log):
        """
        Evaluate a RecordAccessLog instance for suspicious patterns.

        Runs all checks (rule-based + ML), computes a composite suspicion score,
        and returns the score together with a list of string flag names.

        Args:
            access_log: A saved RecordAccessLog instance.

        Returns:
            tuple[int, list[str]]: (score 0-100, list of flag names)
        """
        flags = []

        # Rule-based checks
        if self._is_after_hours(access_log):
            flags.append('after_hours')
        if self._is_bulk_access(access_log):
            flags.append('bulk_access')
        if self._is_cross_department(access_log):
            flags.append('cross_department')
        if self._is_critical_record(access_log):
            flags.append('critical_record')
        if self._is_unknown_device(access_log):
            flags.append('unknown_device')

        # ML-based anomaly detection
        if self._is_ml_anomaly(access_log):
            flags.append('ml_anomaly')

        score = self.calculate_suspicion_score(flags)
        return score, flags

    def calculate_suspicion_score(self, flags):
        """
        Sum weight for each flag, capped at 100.

        Args:
            flags: list of flag name strings (keys in SCORE_WEIGHTS).

        Returns:
            int: suspicion score between 0 and 100.
        """
        total = sum(SCORE_WEIGHTS.get(flag, 0) for flag in flags)
        return min(total, 100)

    def flag_suspicious_activity(self, access_log, score, flags):
        """
        Persist suspicious findings and raise an alert if score >= threshold.

        If score >= SUSPICION_THRESHOLD (40):
          - Sets RecordAccessLog.is_suspicious = True
          - Sets RecordAccessLog.suspicion_reason to the comma-joined flag list
          - Marks the related PatientRecord as is_flagged
          - Creates a SuspiciousActivity record
          - Creates an Alert via the alerts app

        Args:
            access_log: The RecordAccessLog instance being evaluated.
            score:      The suspicion score returned by analyze_access().
            flags:      The flag list returned by analyze_access().

        Returns:
            SuspiciousActivity | None: the created record, or None if below threshold.
        """
        if score < SUSPICION_THRESHOLD:
            return None

        from .models import SuspiciousActivity

        access_log.is_suspicious = True
        access_log.suspicion_reason = ', '.join(flags)
        access_log.save(update_fields=['is_suspicious', 'suspicion_reason'])

        access_log.patient_record.is_flagged = True
        access_log.patient_record.save(update_fields=['is_flagged'])

        activity_type = self._determine_activity_type(flags)
        severity = self._determine_severity(score)
        description = self._build_description(access_log, flags, score)

        activity = SuspiciousActivity.objects.create(
            user=access_log.user,
            activity_type=activity_type,
            description=description,
            severity=severity,
            related_record=access_log.patient_record,
        )

        self._trigger_alert(access_log, activity, score, flags)
        return activity

    def get_activity_summary(self, user, days=7):
        """
        Return a dict with access statistics for a user over the last N days.

        Args:
            user: A User instance.
            days: Integer number of days to look back (default 7).

        Returns:
            dict with keys:
                total_accesses, suspicious_count, access_types (dict),
                hourly_distribution (list[24]), unique_records,
                after_hours_count, suspicious_activities (QuerySet), days.
        """
        from .models import RecordAccessLog, SuspiciousActivity

        since = timezone.now() - timedelta(days=days)
        logs = RecordAccessLog.objects.filter(user=user, timestamp__gte=since)

        total_accesses = logs.count()
        suspicious_count = logs.filter(is_suspicious=True).count()

        access_types = {
            atype: logs.filter(access_type=atype).count()
            for atype in RecordAccessLog.AccessType.values
        }

        hourly = [0] * 24
        for hour_val in logs.values_list('access_hour', flat=True):
            if 0 <= hour_val <= 23:
                hourly[hour_val] += 1

        unique_records = logs.values('patient_record').distinct().count()
        after_hours = (
            logs.filter(access_hour__lt=7).count()
            + logs.filter(access_hour__gt=20).count()
        )

        suspicious_activities = SuspiciousActivity.objects.filter(
            user=user, timestamp__gte=since
        )

        return {
            'total_accesses': total_accesses,
            'suspicious_count': suspicious_count,
            'access_types': access_types,
            'hourly_distribution': hourly,
            'unique_records': unique_records,
            'after_hours_count': after_hours,
            'suspicious_activities': suspicious_activities,
            'days': days,
        }

    # ------------------------------------------------------------------
    # Private checks
    # ------------------------------------------------------------------

    def _is_after_hours(self, access_log):
        """True if access occurred before 07:00 or after 20:00."""
        hour = access_log.access_hour
        return hour < 7 or hour > 20

    def _is_bulk_access(self, access_log):
        """True if the user accessed more than 10 records in the past hour."""
        from .models import RecordAccessLog

        if not access_log.pk:
            return False

        one_hour_ago = timezone.now() - timedelta(hours=1)
        count = RecordAccessLog.objects.filter(
            user=access_log.user,
            timestamp__gte=one_hour_ago,
        ).count()
        return count > 10

    def _is_cross_department(self, access_log):
        """True if the user's department differs from the record's department."""
        if not access_log.user:
            return False
        user_dept = (getattr(access_log.user, 'department', '') or '').strip().lower()
        record_dept = (access_log.patient_record.department or '').strip().lower()
        if not user_dept or not record_dept:
            return False
        return user_dept != record_dept

    def _is_critical_record(self, access_log):
        """True if the accessed record has CRITICAL sensitivity."""
        from .models import PatientRecord
        return access_log.patient_record.sensitivity_level == PatientRecord.SensitivityLevel.CRITICAL

    def _is_unknown_device(self, access_log):
        """True if this device_info string has never been seen before for this user."""
        from .models import RecordAccessLog

        if not access_log.device_info or not access_log.pk:
            return False
        known = RecordAccessLog.objects.filter(
            user=access_log.user,
            device_info=access_log.device_info,
        ).exclude(pk=access_log.pk).exists()
        return not known

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_ml_anomaly(self, access_log):
        """
        Check if the access log is flagged as an anomaly by the ML detector.

        Uses Isolation Forest to detect statistical deviations from normal
        user behavior patterns. Only flags if confidence is high (>50%).

        Returns:
            bool: True if ML detector predicts anomaly with confidence >50%
        """
        try:
            from risk_engine.ml_detector import AnomalyDetector

            detector = AnomalyDetector()
            prediction = detector.predict(access_log)

            if prediction is None:
                return False

            # Flag if anomaly with >50% confidence
            return prediction['is_anomaly'] and prediction['confidence'] > 50

        except Exception:
            # Fail gracefully if ML module not available or model not trained
            return False

    def _determine_activity_type(self, flags):
        """Map the highest-priority flag to a SuspiciousActivity.ActivityType."""
        from .models import SuspiciousActivity

        priority_map = [
            ('bulk_access', SuspiciousActivity.ActivityType.BULK_DOWNLOAD),
            ('cross_department', SuspiciousActivity.ActivityType.CROSS_DEPARTMENT_ACCESS),
            ('after_hours', SuspiciousActivity.ActivityType.AFTER_HOURS_ACCESS),
            ('unknown_device', SuspiciousActivity.ActivityType.UNUSUAL_VOLUME),
            ('critical_record', SuspiciousActivity.ActivityType.UNAUTHORIZED_ATTEMPT),
            ('ml_anomaly', SuspiciousActivity.ActivityType.UNUSUAL_VOLUME),
        ]
        for flag, atype in priority_map:
            if flag in flags:
                return atype
        return SuspiciousActivity.ActivityType.UNUSUAL_VOLUME

    def _determine_severity(self, score):
        """Map a suspicion score to a SuspiciousActivity.Severity level."""
        from .models import SuspiciousActivity

        if score >= 85:
            return SuspiciousActivity.Severity.CRITICAL
        if score >= 60:
            return SuspiciousActivity.Severity.HIGH
        if score >= 40:
            return SuspiciousActivity.Severity.MEDIUM
        return SuspiciousActivity.Severity.LOW

    def _build_description(self, access_log, flags, score):
        """Build a human-readable description for the SuspiciousActivity."""
        flag_labels = {
            'after_hours': 'after-hours access',
            'bulk_access': 'bulk record access (>10 in 1 hour)',
            'cross_department': 'cross-department access',
            'critical_record': 'access to CRITICAL sensitivity record',
            'unknown_device': 'access from unrecognised device',
            'ml_anomaly': 'ML-detected behavioral anomaly',
        }
        flag_text = ', '.join(flag_labels.get(f, f) for f in flags)
        username = access_log.user.username if access_log.user else 'unknown'
        return (
            f"Suspicious activity detected for user '{username}' accessing record "
            f"{access_log.patient_record.patient_code} "
            f"(suspicion score: {score}/100). "
            f"Triggered by: {flag_text}."
        )

    def _trigger_alert(self, access_log, suspicious_activity, score, flags):
        """
        Create an Alert in the alerts subsystem for the suspicious access.

        Uses best-effort creation — failures are silently swallowed to
        avoid breaking the monitoring pipeline if the alerts table is
        unavailable (e.g. during testing with minimal fixtures).
        """
        try:
            from alerts.models import Alert

            severity_map = {
                'CRITICAL': Alert.Severity.CRITICAL,
                'HIGH': Alert.Severity.HIGH,
                'MEDIUM': Alert.Severity.MEDIUM,
                'LOW': Alert.Severity.LOW,
            }
            severity = severity_map.get(suspicious_activity.severity, Alert.Severity.MEDIUM)
            username = access_log.user.username if access_log.user else 'unknown'

            Alert.objects.create(
                title=f'Suspicious Record Access: {access_log.patient_record.patient_code}',
                description=(
                    f"User '{username}' triggered a suspicion score of {score}/100 "
                    f"while accessing patient record "
                    f"{access_log.patient_record.patient_code}. "
                    f"Flags: {', '.join(flags)}."
                ),
                alert_type=Alert.AlertType.DATA_BREACH,
                severity=severity,
            )
        except Exception:
            pass
