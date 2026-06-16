"""
risk_engine/engine.py
=====================
RiskIntelligenceEngine — core analytics and detection logic for the
HealthSec cyber risk platform.

The engine is stateless: instantiate it on demand and pass querysets /
model instances as arguments rather than storing state between calls.

Usage::

    from risk_engine.engine import RiskIntelligenceEngine

    engine = RiskIntelligenceEngine()
    score  = engine.calculate_risk_score(ThreatEvent.objects.filter(status='OPEN'))
    level  = engine.classify_risk_level(score)
    report = engine.generate_risk_assessment(requested_by=request.user)
"""

import logging
from collections import defaultdict
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from .constants import SEVERITY_WEIGHTS, RISK_THRESHOLDS, THREAT_TYPE_MITRE_MAP

logger = logging.getLogger('healthsec.risk_engine')
User = get_user_model()


class RiskIntelligenceEngine:
    """
    Central analytics engine for the HealthSec cyber risk intelligence module.

    All public methods are independently callable and can be unit-tested
    without side effects (except those that explicitly write to the database,
    which are clearly documented).
    """

    # ------------------------------------------------------------------
    # 1. Risk score calculation
    # ------------------------------------------------------------------

    def calculate_risk_score(self, threat_events_queryset) -> float:
        """
        Compute a 0-100 composite risk score from a set of threat events.

        Formula:
            weighted_sum = Σ (event.risk_score × severity_weight)
            max_possible = Σ (100 × CRITICAL_weight) for every event
            score        = (weighted_sum / max_possible) × 100

        This gives the *percentage of the worst-case scenario* represented
        by the current threat landscape, which is intuitive and auditable.

        Args:
            threat_events_queryset: A queryset or list of ThreatEvent instances.

        Returns:
            float: Composite risk score in [0.0, 100.0].
        """
        events = list(threat_events_queryset)
        if not events:
            return 0.0

        critical_weight = SEVERITY_WEIGHTS[4]  # 1.0
        weighted_sum = sum(
            e.risk_score * SEVERITY_WEIGHTS.get(e.severity, 0.1)
            for e in events
        )
        max_possible = len(events) * 100.0 * critical_weight
        if max_possible == 0:
            return 0.0

        score = (weighted_sum / max_possible) * 100.0
        return round(min(score, 100.0), 2)

    # ------------------------------------------------------------------
    # 2. Risk level classification
    # ------------------------------------------------------------------

    def classify_risk_level(self, score: float) -> str:
        """
        Map a 0-100 numeric score to a named risk level.

        Thresholds:
            0–25  → LOW      (green)
            26–50 → MEDIUM   (yellow)
            51–75 → HIGH     (orange)
            76–100 → CRITICAL (red)

        Args:
            score: A float in [0.0, 100.0].

        Returns:
            str: One of 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.
        """
        if score <= 25:
            return 'LOW'
        if score <= 50:
            return 'MEDIUM'
        if score <= 75:
            return 'HIGH'
        return 'CRITICAL'

    # ------------------------------------------------------------------
    # 3. Brute-force detection
    # ------------------------------------------------------------------

    def detect_brute_force(self, user_id: int, time_window_minutes: int = 10):
        """
        Check for brute-force login activity against a user account.

        Uses UserProfile.failed_login_attempts and last_failed_login as a
        proxy for a LoginHistory table (which is not present in this project).
        If the user has ≥5 failed attempts within the time window, a
        ThreatEvent of type BRUTE_FORCE is created.

        Args:
            user_id:             Primary key of the target User.
            time_window_minutes: Look-back window in minutes (default 10).

        Returns:
            ThreatEvent | None: The created event, or None if no threat detected.
        """
        from accounts.models import UserProfile
        from .models import ThreatEvent

        try:
            profile = UserProfile.objects.select_related('user').get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None

        if profile.failed_login_attempts < 5:
            return None

        if not profile.last_failed_login:
            return None

        cutoff = timezone.now() - timedelta(minutes=time_window_minutes)
        if profile.last_failed_login < cutoff:
            return None

        tactic_id, technique_id, technique_name = THREAT_TYPE_MITRE_MAP['BRUTE_FORCE']
        event = ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.BRUTE_FORCE,
            target_user=profile.user,
            target_resource=f'Login endpoint — account: {profile.user.username}',
            severity=ThreatEvent.Severity.HIGH,
            risk_score=75.0,
            description=(
                f"Brute-force attack detected against '{profile.user.username}': "
                f"{profile.failed_login_attempts} failed login attempts within "
                f"{time_window_minutes} minutes."
            ),
            indicators={
                'failed_attempts': profile.failed_login_attempts,
                'last_failed_login': str(profile.last_failed_login),
                'time_window_minutes': time_window_minutes,
            },
            mitre_tactic=f'{tactic_id} — {technique_id}: {technique_name}',
        )
        logger.warning(
            'Brute-force event created for user %s (%d attempts)',
            profile.user.username, profile.failed_login_attempts,
        )
        return event

    # ------------------------------------------------------------------
    # 4. Unusual access pattern detection
    # ------------------------------------------------------------------

    def detect_unusual_access_pattern(self, user_id: int):
        """
        Scan a user's patient record access logs for anomalous patterns.

        Checks performed:
          - Volume spike: today's access count > 3× the 7-day daily average
          - After-hours pattern: ≥5 accesses outside 07:00–20:00 in last 7 days
          - Cross-department access: any access where user dept ≠ record dept

        A ThreatEvent is created for each detected anomaly.

        Args:
            user_id: Primary key of the target User.

        Returns:
            list[ThreatEvent]: All events created (may be empty).
        """
        from monitoring.models import RecordAccessLog
        from .models import ThreatEvent

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return []

        events_created = []
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        logs = RecordAccessLog.objects.filter(user=user, timestamp__gte=week_ago)

        # --- Volume spike ---
        today_count = logs.filter(timestamp__date=now.date()).count()
        week_count = logs.count()
        daily_avg = week_count / 7.0 if week_count > 0 else 0

        if daily_avg > 0 and today_count > daily_avg * 3:
            tactic_id, technique_id, technique_name = THREAT_TYPE_MITRE_MAP['ANOMALOUS_BEHAVIOR']
            evt = ThreatEvent.objects.create(
                threat_type=ThreatEvent.ThreatType.ANOMALOUS_BEHAVIOR,
                target_user=user,
                target_resource='Patient Record System',
                severity=ThreatEvent.Severity.MEDIUM,
                risk_score=55.0,
                description=(
                    f"Access volume spike for '{user.username}': "
                    f"{today_count} accesses today vs {daily_avg:.1f} daily average "
                    f"({today_count / daily_avg:.1f}× normal rate)."
                ),
                indicators={
                    'today_count': today_count,
                    'daily_avg': round(daily_avg, 2),
                    'spike_ratio': round(today_count / daily_avg, 2),
                },
                mitre_tactic=f'{tactic_id} — {technique_id}: {technique_name}',
            )
            events_created.append(evt)

        # --- After-hours pattern ---
        after_hours = (
            logs.filter(access_hour__lt=7).count()
            + logs.filter(access_hour__gt=20).count()
        )
        if after_hours >= 5:
            tactic_id, technique_id, technique_name = THREAT_TYPE_MITRE_MAP['UNAUTHORIZED_ACCESS']
            evt = ThreatEvent.objects.create(
                threat_type=ThreatEvent.ThreatType.UNAUTHORIZED_ACCESS,
                target_user=user,
                target_resource='Patient Record System (Off-hours)',
                severity=ThreatEvent.Severity.HIGH,
                risk_score=70.0,
                description=(
                    f"Persistent after-hours access for '{user.username}': "
                    f"{after_hours} accesses outside 07:00–20:00 in the last 7 days."
                ),
                indicators={'after_hours_count': after_hours, 'window_days': 7},
                mitre_tactic=f'{tactic_id} — {technique_id}: {technique_name}',
            )
            events_created.append(evt)

        # --- Cross-department access ---
        if hasattr(user, 'department') and user.department:
            cross_dept = logs.exclude(
                patient_record__department__iexact=user.department
            ).count()
            if cross_dept >= 3:
                tactic_id, technique_id, technique_name = THREAT_TYPE_MITRE_MAP['INSIDER_THREAT']
                evt = ThreatEvent.objects.create(
                    threat_type=ThreatEvent.ThreatType.INSIDER_THREAT,
                    target_user=user,
                    target_resource=f'Records outside {user.department} department',
                    severity=ThreatEvent.Severity.MEDIUM,
                    risk_score=50.0,
                    description=(
                        f"Cross-department access for '{user.username}' "
                        f"(dept: {user.department}): {cross_dept} accesses to "
                        f"records belonging to other departments."
                    ),
                    indicators={
                        'user_department': user.department,
                        'cross_dept_count': cross_dept,
                    },
                    mitre_tactic=f'{tactic_id} — {technique_id}: {technique_name}',
                )
                events_created.append(evt)

        return events_created

    # ------------------------------------------------------------------
    # 5. Threat feed IP check
    # ------------------------------------------------------------------

    def check_threat_feed(self, ip_address: str):
        """
        Cross-reference an IP address against the active ThreatFeed entries.

        Checks for exact IP matches. If found, creates a ThreatEvent with
        HIGH severity and returns the match details.

        Args:
            ip_address: IPv4 or IPv6 address string to look up.

        Returns:
            tuple[bool, float]: (is_malicious, confidence_score)
                is_malicious    – True if the IP appears in the feed
                confidence_score – 0.0 if not found, else the highest confidence
        """
        from .models import ThreatFeed, ThreatEvent

        if not ip_address:
            return False, 0.0

        matches = ThreatFeed.objects.filter(
            threat_indicator=ip_address,
            indicator_type=ThreatFeed.IndicatorType.IP,
            is_active=True,
        ).order_by('-confidence_score')

        if not matches.exists():
            return False, 0.0

        best = matches.first()
        tactic_id, technique_id, technique_name = THREAT_TYPE_MITRE_MAP['UNAUTHORIZED_ACCESS']

        ThreatEvent.objects.create(
            threat_type=ThreatEvent.ThreatType.UNAUTHORIZED_ACCESS,
            source_ip=ip_address,
            target_resource='Network Perimeter',
            severity=ThreatEvent.Severity.HIGH,
            risk_score=best.confidence_score,
            description=(
                f"Known-malicious IP address {ip_address} detected in threat feed "
                f"'{best.feed_name}' (category: {best.threat_category}, "
                f"confidence: {best.confidence_score:.0f}%)."
            ),
            indicators={
                'ip_address': ip_address,
                'feed_name': best.feed_name,
                'threat_category': best.threat_category,
                'confidence': best.confidence_score,
                'source': best.source,
            },
            mitre_tactic=f'{tactic_id} — {technique_id}: {technique_name}',
        )

        logger.info('Threat feed match for IP %s — confidence %.0f%%', ip_address, best.confidence_score)
        return True, best.confidence_score

    # ------------------------------------------------------------------
    # 6. Full risk assessment generation
    # ------------------------------------------------------------------

    def generate_risk_assessment(self, requested_by=None) -> dict:
        """
        Aggregate all open ThreatEvents into a RiskAssessment record.

        Calculates the composite score, classifies the risk level, identifies
        top threats, and writes recommendations.  Persists a RiskAssessment
        record and returns a summary dict.

        Args:
            requested_by: The User who triggered the assessment (may be None).

        Returns:
            dict: Assessment summary (mirrors RiskAssessment fields plus
                  'assessment' key holding the saved instance).
        """
        from .models import ThreatEvent, RiskAssessment

        open_events = ThreatEvent.objects.filter(
            status__in=[ThreatEvent.Status.OPEN, ThreatEvent.Status.INVESTIGATING]
        )

        score = self.calculate_risk_score(open_events)
        level = self.classify_risk_level(score)

        # Counts per severity
        counts_by_severity = {
            'LOW':      open_events.filter(severity=ThreatEvent.Severity.LOW).count(),
            'MEDIUM':   open_events.filter(severity=ThreatEvent.Severity.MEDIUM).count(),
            'HIGH':     open_events.filter(severity=ThreatEvent.Severity.HIGH).count(),
            'CRITICAL': open_events.filter(severity=ThreatEvent.Severity.CRITICAL).count(),
        }

        # Top 5 highest-risk events
        top_events = open_events.order_by('-severity', '-risk_score')[:5]
        top_threats_data = [
            {
                'id': str(e.threat_id),
                'type': e.get_threat_type_display(),
                'severity': e.get_severity_display(),
                'risk_score': e.risk_score,
                'target': e.target_resource,
            }
            for e in top_events
        ]

        recommendations = self._build_recommendations(level, counts_by_severity)
        next_due = (timezone.now() + timedelta(days=30)).date()

        assessment = RiskAssessment.objects.create(
            conducted_by=requested_by,
            overall_risk_score=score,
            risk_level=level,
            threat_count_by_severity=counts_by_severity,
            top_threats=top_threats_data,
            recommendations=recommendations,
            next_assessment_due=next_due,
        )

        logger.info(
            'Risk assessment generated: score=%.1f level=%s open_threats=%d',
            score, level, open_events.count(),
        )

        return {
            'assessment': assessment,
            'score': score,
            'level': level,
            'counts_by_severity': counts_by_severity,
            'top_threats': top_threats_data,
            'recommendations': recommendations,
            'next_due': next_due,
            'total_open': open_events.count(),
        }

    # ------------------------------------------------------------------
    # 7. Threat timeline
    # ------------------------------------------------------------------

    def get_threat_timeline(self, days: int = 30) -> dict:
        """
        Return a date-keyed dict of daily threat counts for the last N days.

        Useful for rendering line/bar charts in templates.

        Args:
            days: Number of days to look back.

        Returns:
            dict: {date_str: count} sorted oldest-first.
                  e.g. {'2024-01-01': 3, '2024-01-02': 7, ...}
        """
        from .models import ThreatEvent

        since = timezone.now() - timedelta(days=days)
        qs = (
            ThreatEvent.objects
            .filter(detected_at__gte=since)
            .extra(select={'day': 'date(detected_at)'})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Fill every day in the range (even zero-count days)
        result = {}
        for i in range(days):
            d = (timezone.now() - timedelta(days=days - 1 - i)).date()
            result[str(d)] = 0
        for row in qs:
            result[str(row['day'])] = row['count']

        return result

    # ------------------------------------------------------------------
    # 8. Threat heatmap
    # ------------------------------------------------------------------

    def get_threat_heatmap_data(self) -> list:
        """
        Return a 7×24 matrix of threat frequencies for the last 90 days.

        Rows  = day of week (0=Monday … 6=Sunday)
        Cols  = hour of day (0 … 23)
        Value = number of ThreatEvents detected in that slot

        Useful for rendering heatmap visualisations in templates.

        Returns:
            list[list[int]]: 7 rows × 24 columns, all non-negative integers.
        """
        from .models import ThreatEvent

        matrix = [[0] * 24 for _ in range(7)]
        since = timezone.now() - timedelta(days=90)

        for event in ThreatEvent.objects.filter(detected_at__gte=since).only('detected_at'):
            dow = event.detected_at.weekday()  # 0=Mon
            hour = event.detected_at.hour
            matrix[dow][hour] += 1

        return matrix

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_recommendations(self, level: str, counts: dict) -> str:
        """Generate a text block of recommendations based on the risk level."""
        lines = [f'Overall risk level: {level}', '']

        if level == 'CRITICAL':
            lines += [
                '• IMMEDIATE ACTION REQUIRED: Activate the Incident Response Plan.',
                '• Convene the security team for an emergency triage session.',
                '• Isolate any systems involved in CRITICAL-severity events.',
                '• Notify senior management and the Data Protection Officer.',
            ]
        elif level == 'HIGH':
            lines += [
                '• Assign all HIGH and CRITICAL threats to senior analysts.',
                '• Review and tighten access controls across PHI-bearing systems.',
                '• Schedule a penetration test within 14 days.',
            ]
        elif level == 'MEDIUM':
            lines += [
                '• Review all OPEN threats and close or escalate within 48 hours.',
                '• Verify patch status for all known VulnerabilityRecord entries.',
                '• Conduct a targeted phishing awareness campaign.',
            ]
        else:
            lines += [
                '• Maintain current security posture.',
                '• Continue regular monitoring and log review.',
                '• Ensure next assessment is scheduled within 30 days.',
            ]

        lines += [
            '',
            f'Threat breakdown: '
            f'CRITICAL={counts["CRITICAL"]}  HIGH={counts["HIGH"]}  '
            f'MEDIUM={counts["MEDIUM"]}  LOW={counts["LOW"]}',
        ]
        return '\n'.join(lines)
