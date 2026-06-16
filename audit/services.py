"""
audit/services.py
=================
Business logic for audit logging and tamper detection.

AuditService provides:
- Centralized audit log creation with checksum generation
- Cryptographic integrity verification
- Periodic integrity check runs
- Statistics and reporting
"""

import hashlib
import json
import logging
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import AuditLog, AuditLogIntegrityCheck

User = get_user_model()
logger = logging.getLogger(__name__)


class AuditService:
    """Service layer for audit logging and integrity management."""

    @staticmethod
    def generate_checksum(log_data):
        """
        Generate SHA256 checksum for audit log entry.

        Args:
            log_data (dict): Dictionary containing log entry data

        Returns:
            str: SHA256 hex digest
        """
        data_string = json.dumps(log_data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()

    @staticmethod
    @transaction.atomic
    def log(user=None, action_category=AuditLog.ActionCategory.SYSTEM, action='',
            description='', target_model='', target_id='',
            old_value=None, new_value=None,
            ip_address=None, user_agent='', session_key='',
            status=AuditLog.Status.SUCCESS):
        """
        Create an immutable audit log entry with checksum.

        Args:
            user: User instance who performed action (None for system actions)
            action_category: Category of action (from ActionCategory choices)
            action: Specific action name
            description: Human-readable description of action
            target_model: Model name that was affected
            target_id: Primary key of affected object
            old_value: JSON-serializable data before change
            new_value: JSON-serializable data after change
            ip_address: Client IP address
            user_agent: HTTP User-Agent header
            session_key: Django session key
            status: SUCCESS, FAILURE, or ERROR

        Returns:
            AuditLog: The created audit log instance
        """
        timestamp = timezone.now()

        log_data_for_checksum = {
            'user_id': user.id if user else None,
            'action_category': action_category,
            'action': action,
            'description': description,
            'target_model': target_model,
            'target_id': target_id,
            'timestamp': timestamp.isoformat(),
            'status': status,
        }

        checksum = AuditService.generate_checksum(log_data_for_checksum)

        audit_log = AuditLog.objects.create(
            user=user,
            action_category=action_category,
            action=action,
            description=description,
            target_model=target_model,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key,
            status=status,
            checksum=checksum,
            timestamp=timestamp,
        )

        logger.info(
            f'Audit log created: {action} by {user.username if user else "System"} '
            f'(status: {status})'
        )

        return audit_log

    @staticmethod
    def verify_integrity(log_instance):
        """
        Verify that an audit log entry has not been tampered with.

        Recomputes the checksum from the stored data and compares it
        against the stored checksum. Any mismatch indicates tampering.

        Args:
            log_instance: AuditLog instance to verify

        Returns:
            bool: True if checksum matches (log is intact), False if tampered
        """
        log_data_for_checksum = {
            'user_id': log_instance.user_id,
            'action_category': log_instance.action_category,
            'action': log_instance.action,
            'description': log_instance.description,
            'target_model': log_instance.target_model,
            'target_id': log_instance.target_id,
            'timestamp': log_instance.timestamp.isoformat(),
            'status': log_instance.status,
        }

        computed_checksum = AuditService.generate_checksum(log_data_for_checksum)
        return computed_checksum == log_instance.checksum

    @staticmethod
    @transaction.atomic
    def run_integrity_check(checked_by_user):
        """
        Run comprehensive integrity check on all audit logs.

        Verifies the checksum of every audit log entry. If any entries
        have invalid checksums, they are flagged as corrupted.

        Args:
            checked_by_user: User instance who initiated the check

        Returns:
            dict: Summary of check results with keys:
                - total_logs: Total number of logs checked
                - corrupted_logs: Number of logs with invalid checksums
                - tampered_log_ids: List of corrupted log IDs
                - result: INTACT, TAMPERED, or ERROR
                - check_record: AuditLogIntegrityCheck instance
        """
        try:
            all_logs = AuditLog.objects.all()
            total_logs = all_logs.count()
            corrupted_logs = []

            for log in all_logs:
                if not AuditService.verify_integrity(log):
                    corrupted_logs.append(str(log.log_id))

            result = (
                AuditLogIntegrityCheck.Result.INTACT
                if len(corrupted_logs) == 0
                else AuditLogIntegrityCheck.Result.TAMPERED
            )

            details = (
                f'Checked {total_logs} logs. '
                f'{len(corrupted_logs)} logs with invalid checksums detected.'
            )
            if corrupted_logs:
                details += f'\nTampered logs: {", ".join(corrupted_logs[:10])}'
                if len(corrupted_logs) > 10:
                    details += f'\n... and {len(corrupted_logs) - 10} more'

            check_record = AuditLogIntegrityCheck.objects.create(
                checked_by=checked_by_user,
                total_logs_checked=total_logs,
                corrupted_logs=len(corrupted_logs),
                result=result,
                details=details,
            )

            logger.info(
                f'Integrity check completed by {checked_by_user.username}: '
                f'{total_logs} logs checked, {len(corrupted_logs)} corrupted'
            )

            return {
                'total_logs': total_logs,
                'corrupted_logs': len(corrupted_logs),
                'tampered_log_ids': corrupted_logs,
                'result': result,
                'check_record': check_record,
            }

        except Exception as e:
            logger.error(f'Error during integrity check: {str(e)}')
            check_record = AuditLogIntegrityCheck.objects.create(
                checked_by=checked_by_user,
                total_logs_checked=0,
                corrupted_logs=0,
                result=AuditLogIntegrityCheck.Result.ERROR,
                details=f'Error during integrity check: {str(e)}',
            )
            return {
                'total_logs': 0,
                'corrupted_logs': 0,
                'tampered_log_ids': [],
                'result': AuditLogIntegrityCheck.Result.ERROR,
                'check_record': check_record,
            }

    @staticmethod
    def get_statistics(days=30):
        """
        Get audit statistics for reporting and dashboards.

        Args:
            days: Number of days to include in analysis

        Returns:
            dict: Statistics including counts by category, user, status
        """
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=days)
        logs = AuditLog.objects.filter(timestamp__gte=cutoff)

        stats = {
            'total_logs': logs.count(),
            'logs_by_category': {
                choice[0]: logs.filter(action_category=choice[0]).count()
                for choice in AuditLog.ActionCategory.choices
            },
            'logs_by_status': {
                choice[0]: logs.filter(status=choice[0]).count()
                for choice in AuditLog.Status.choices
            },
            'logs_by_user': {},
            'unique_users': logs.values('user').distinct().count(),
            'success_rate': round(
                (logs.filter(status=AuditLog.Status.SUCCESS).count() / max(logs.count(), 1)) * 100,
                2
            ),
        }

        # Top 10 users
        top_users = logs.values('user__username').annotate(
            count=models.Count('log_id')
        ).order_by('-count')[:10]

        for user_entry in top_users:
            if user_entry['user__username']:
                stats['logs_by_user'][user_entry['user__username']] = user_entry['count']
            else:
                stats['logs_by_user']['[System]'] = user_entry['count']

        return stats

    @staticmethod
    def export_logs(queryset, format='csv'):
        """
        Export audit logs to CSV or JSON format.

        Args:
            queryset: QuerySet of AuditLog instances
            format: 'csv' or 'json'

        Returns:
            str: Formatted export data
        """
        if format == 'json':
            logs_data = [
                {
                    'log_id': str(log.log_id),
                    'timestamp': log.timestamp.isoformat(),
                    'user': log.user.username if log.user else 'System',
                    'action_category': log.action_category,
                    'action': log.action,
                    'description': log.description,
                    'target_model': log.target_model,
                    'target_id': log.target_id,
                    'status': log.status,
                    'ip_address': log.ip_address,
                    'checksum_valid': AuditService.verify_integrity(log),
                }
                for log in queryset
            ]
            return json.dumps(logs_data, indent=2, default=str)

        elif format == 'csv':
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    'Timestamp', 'User', 'Action Category', 'Action',
                    'Description', 'Target Model', 'Target ID', 'Status',
                    'IP Address', 'Checksum Valid'
                ]
            )
            writer.writeheader()

            for log in queryset:
                writer.writerow({
                    'Timestamp': log.timestamp.isoformat(),
                    'User': log.user.username if log.user else 'System',
                    'Action Category': log.get_action_category_display(),
                    'Action': log.action,
                    'Description': log.description,
                    'Target Model': log.target_model,
                    'Target ID': log.target_id,
                    'Status': log.get_status_display(),
                    'IP Address': log.ip_address or '—',
                    'Checksum Valid': '✓' if AuditService.verify_integrity(log) else '✗',
                })

            return output.getvalue()

        return ''
