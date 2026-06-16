"""
audit/decorators.py
===================
Decorators for automatic audit logging of view functions and model changes.

Usage:
    @audit_action(category=AuditLog.ActionCategory.ALERT, action='alert_resolve')
    def resolve_alert(request, alert_id):
        ...
"""

import functools
import logging
from django.core.exceptions import PermissionDenied
from .services import AuditService
from .models import AuditLog

logger = logging.getLogger(__name__)


def audit_action(category, action, description=''):
    """
    Decorator to automatically log a view function or method execution.

    Args:
        category: Action category (from AuditLog.ActionCategory)
        action: Specific action name
        description: Description template (can include {object} placeholder)

    Returns:
        Decorator function
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                # Execute the view function
                result = func(request, *args, **kwargs)

                # Log successful execution
                desc = description or f'{action} executed'
                if request.user and request.user.is_authenticated:
                    AuditService.log(
                        user=request.user,
                        action_category=category,
                        action=action,
                        description=desc,
                        ip_address=_get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        session_key=request.session.session_key if request.session else '',
                        status=AuditLog.Status.SUCCESS,
                    )

                return result

            except PermissionDenied as e:
                # Log permission failures
                AuditService.log(
                    user=request.user if request.user.is_authenticated else None,
                    action_category=category,
                    action=action,
                    description=f'{description} - Permission Denied: {str(e)}',
                    ip_address=_get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    session_key=request.session.session_key if request.session else '',
                    status=AuditLog.Status.FAILURE,
                )
                raise

            except Exception as e:
                # Log unexpected errors
                AuditService.log(
                    user=request.user if request.user.is_authenticated else None,
                    action_category=category,
                    action=action,
                    description=f'{description} - Error: {str(e)}',
                    ip_address=_get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    session_key=request.session.session_key if request.session else '',
                    status=AuditLog.Status.ERROR,
                )
                raise

        return wrapper

    return decorator


def audit_model_change(action, target_model, description=''):
    """
    Decorator to log model creation/update with before/after values.

    Args:
        action: Action name (e.g., 'create', 'update')
        target_model: Model class that was changed
        description: Description template

    Returns:
        Decorator function
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                result = func(request, *args, **kwargs)

                # Log successful model change
                desc = description or f'{action} {target_model.__name__}'
                if request.user and request.user.is_authenticated:
                    AuditService.log(
                        user=request.user,
                        action_category=AuditLog.ActionCategory.DATA_MODIFICATION,
                        action=action,
                        description=desc,
                        target_model=target_model.__name__,
                        ip_address=_get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        session_key=request.session.session_key if request.session else '',
                        status=AuditLog.Status.SUCCESS,
                    )

                return result

            except Exception as e:
                # Log failures
                AuditService.log(
                    user=request.user if request.user.is_authenticated else None,
                    action_category=AuditLog.ActionCategory.DATA_MODIFICATION,
                    action=action,
                    description=f'{description} - Error: {str(e)}',
                    target_model=target_model.__name__,
                    ip_address=_get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    session_key=request.session.session_key if request.session else '',
                    status=AuditLog.Status.ERROR,
                )
                raise

        return wrapper

    return decorator


def _get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')
