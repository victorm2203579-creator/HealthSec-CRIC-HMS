"""
alerts/context_processors.py
=============================
Injects system-wide notification data into every template context.
Covers alerts, open incidents, compliance failures, and high-risk systems.
"""

from .models import Alert, Incident


def unread_alerts_count(request):
    """Return notification counts and items for the topbar bell dropdown."""
    if not request.user.is_authenticated:
        return {
            'unread_alerts_count': 0,
            'notifications_total': 0,
            'notifications': [],
        }

    notifications = []

    try:
        # 1. New (unread) alerts
        new_alerts = Alert.objects.filter(
            status=Alert.Status.NEW
        ).select_related('affected_system').order_by('-created_at')[:5]

        unread_count = Alert.objects.filter(status=Alert.Status.NEW).count()

        for alert in new_alerts:
            level = alert.severity.lower() if alert.severity else 'info'
            colour = {
                'critical': '#dc3545',
                'high':     '#fd7e14',
                'medium':   '#ffc107',
                'low':      '#198754',
            }.get(level, '#6c757d')
            notifications.append({
                'type':    'alert',
                'icon':    'bell',
                'colour':  colour,
                'title':   alert.title,
                'sub':     f'{alert.severity} · {alert.get_alert_type_display()}',
                'url':     f'/alerts/{alert.pk}/',
                'age':     alert.created_at,
            })

        # 2. Open incidents
        open_incidents = Incident.objects.exclude(
            phase='CLOSED'
        ).order_by('-detected_at')[:3]
        incident_count = Incident.objects.exclude(phase='CLOSED').count()

        for inc in open_incidents:
            notifications.append({
                'type':    'incident',
                'icon':    'flame',
                'colour':  '#dc3545',
                'title':   inc.title,
                'sub':     f'Incident · {inc.phase}',
                'url':     f'/alerts/incidents/{inc.pk}/',
                'age':     inc.detected_at,
            })

        # 3. Compliance failures (recent)
        try:
            from compliance.models import ControlAssessment
            fail_count = ControlAssessment.objects.filter(status='FAIL').count()
            if fail_count:
                notifications.append({
                    'type':    'compliance',
                    'icon':    'shield-x',
                    'colour':  '#ffc107',
                    'title':   f'{fail_count} Compliance Control{"s" if fail_count != 1 else ""} Failing',
                    'sub':     'Compliance · Action required',
                    'url':     '/compliance/summary/',
                    'age':     None,
                })
        except Exception:
            fail_count = 0

        # 4. High-risk systems
        try:
            from risk_engine.models import RiskScore
            high_risk = RiskScore.objects.filter(
                risk_level__in=['CRITICAL', 'HIGH']
            ).count()
            if high_risk:
                notifications.append({
                    'type':    'risk',
                    'icon':    'activity',
                    'colour':  '#fd7e14',
                    'title':   f'{high_risk} High-Risk System{"s" if high_risk != 1 else ""}',
                    'sub':     'Risk Engine · Review required',
                    'url':     '/risk/',
                    'age':     None,
                })
        except Exception:
            high_risk = 0

        # Sort by age (None ages go last)
        notifications.sort(key=lambda n: (n['age'] is None, n['age'] and -n['age'].timestamp() or 0))

        total = unread_count + incident_count

    except Exception:
        unread_count = 0
        total = 0

    return {
        'unread_alerts_count': unread_count,
        'notifications_total': total,
        'notifications': notifications[:8],
    }
