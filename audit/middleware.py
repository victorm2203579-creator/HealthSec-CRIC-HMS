"""
audit/middleware.py
===================
WSGI middleware for automatic audit logging of HTTP requests.

Logs all POST, PUT, PATCH, and DELETE requests with user, IP, and status.
Skips static files, health checks, and media files.
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from .services import AuditService
from .models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware that automatically logs all write (POST, PUT, DELETE) HTTP requests.

    Captures request metadata (IP, user-agent, session) and response status code
    for audit trail. Skips static files, media files, and health checks.
    """

    SKIPPED_PATHS = [
        '/static/',
        '/media/',
        '/health/',
        '/__healthcheck__/',
        '/favicon.ico',
        '/robots.txt',
    ]

    def process_request(self, request):
        """Capture request metadata for later logging."""
        request._audit_method = request.method
        request._audit_path = request.path
        request._audit_ip = self._get_client_ip(request)
        request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')
        try:
            request._audit_session = request.session.session_key or ''
        except Exception:
            request._audit_session = ''
        return None

    def process_response(self, request, response):
        """Log write requests (POST, PUT, DELETE, PATCH) after response."""
        if not hasattr(request, '_audit_method'):
            return response

        # Only log write methods
        if request._audit_method not in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return response

        # Skip certain paths
        if any(request._audit_path.startswith(path) for path in self.SKIPPED_PATHS):
            return response

        # Skip API endpoints (they log their own actions)
        if request._audit_path.startswith('/api/'):
            return response

        try:
            # Determine action category and name from request
            action_category, action_name = self._categorize_request(request)

            # Determine status
            status = self._get_status_from_response(response)

            # Log the action
            if request.user and request.user.is_authenticated:
                AuditService.log(
                    user=request.user,
                    action_category=action_category,
                    action=action_name,
                    description=f'{request._audit_method} {request._audit_path}',
                    ip_address=request._audit_ip,
                    user_agent=request._audit_user_agent,
                    session_key=request._audit_session,
                    status=status,
                )

        except Exception as e:
            logger.error(f'Error logging audit event: {str(e)}')

        return response

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def _categorize_request(request):
        """Categorize request based on path and method."""
        path = request.path.lower()

        if '/accounts/' in path:
            return (AuditLog.ActionCategory.AUTH, f'{request.method} User Action')
        elif '/monitoring/' in path:
            return (AuditLog.ActionCategory.DATA_ACCESS, f'{request.method} Monitoring Data')
        elif '/risk/' in path:
            return (AuditLog.ActionCategory.DATA_MODIFICATION, f'{request.method} Risk Data')
        elif '/compliance/' in path:
            return (AuditLog.ActionCategory.COMPLIANCE, f'{request.method} Compliance Data')
        elif '/alerts/' in path:
            return (AuditLog.ActionCategory.ALERT, f'{request.method} Alert')
        elif '/admin/' in path:
            return (AuditLog.ActionCategory.CONFIGURATION, f'{request.method} Admin')
        else:
            return (AuditLog.ActionCategory.SYSTEM, f'{request.method} System Action')

    @staticmethod
    def _get_status_from_response(response):
        """Determine audit status from HTTP response code."""
        status_code = response.status_code
        if status_code < 400:
            return AuditLog.Status.SUCCESS
        elif status_code < 500:
            return AuditLog.Status.FAILURE
        else:
            return AuditLog.Status.ERROR
