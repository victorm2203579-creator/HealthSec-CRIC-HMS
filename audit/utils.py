"""
audit/utils.py
==============
Helper function used throughout the project to write audit log entries.

Usage:
    from audit.utils import log_event

    log_event(
        action='ALERT_ACK',
        description='Alert #42 acknowledged.',
        user=request.user,
        request=request,
        action_category='ALERT',
        extra_data={'alert_id': 42},
    )
"""

import logging

from .models import AuditLog

logger = logging.getLogger('healthsec.audit')


def log_event(
    action: str,
    description: str,
    user=None,
    request=None,
    action_category: str = AuditLog.ActionCategory.SYSTEM,
    status: str = AuditLog.Status.SUCCESS,
    extra_data: dict | None = None,
    target_model: str = '',
    target_id: str = '',
    old_value=None,
    new_value=None,
) -> AuditLog | None:
    """
    Create an AuditLog entry.

    Parameters
    ----------
    action          : Short action identifier string (e.g. 'LOGIN', 'ALERT_ACK').
    description     : Human-readable explanation of the event.
    user            : The User instance responsible (or None for system actions).
    request         : The Django HttpRequest (used to extract IP, UA, session).
    action_category : AuditLog.ActionCategory choice (default: SYSTEM).
    status          : AuditLog.Status choice (default: SUCCESS).
    extra_data      : Optional dict of additional structured context (stored in new_value).
    target_model    : Model class name the action affected (e.g. 'Alert').
    target_id       : PK of the affected object.
    old_value       : Pre-change state for modification tracking.
    new_value       : Post-change state (overridden by extra_data if both provided).

    Returns the created AuditLog instance, or None if creation fails.
    """
    try:
        ip_address = None
        user_agent = ''
        session_key = ''

        if request is not None:
            ip_address = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            if user is None and hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            try:
                session_key = request.session.session_key or ''
            except Exception:
                session_key = ''

        return AuditLog.objects.create(
            user=user,
            action_category=action_category,
            action=action,
            description=description,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key,
            target_model=target_model,
            target_id=str(target_id) if target_id else '',
            old_value=old_value,
            new_value=new_value if new_value is not None else extra_data,
        )

    except Exception as exc:
        logger.error('Failed to write audit log entry: %s', exc)
        return None


def _get_client_ip(request) -> str | None:
    """Extract the real client IP, respecting X-Forwarded-For headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
