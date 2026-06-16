"""
audit/serializers.py
====================
DRF serializers for audit log API endpoints.
"""

from rest_framework import serializers
from .models import AuditLog, AuditLogIntegrityCheck


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""

    user_username = serializers.CharField(source='user.username', read_only=True)
    integrity_valid = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'log_id', 'user', 'user_username', 'action_category', 'action',
            'description', 'target_model', 'target_id', 'old_value', 'new_value',
            'ip_address', 'user_agent', 'session_key', 'timestamp', 'status',
            'checksum', 'integrity_valid'
        ]
        read_only_fields = ['log_id', 'timestamp', 'checksum', 'integrity_valid']

    def get_integrity_valid(self, obj):
        """Check if log entry's checksum is valid."""
        from .services import AuditService
        return AuditService.verify_integrity(obj)


class AuditLogIntegrityCheckSerializer(serializers.ModelSerializer):
    """Serializer for AuditLogIntegrityCheck model."""

    checked_by_username = serializers.CharField(source='checked_by.username', read_only=True)

    class Meta:
        model = AuditLogIntegrityCheck
        fields = [
            'check_id', 'checked_at', 'checked_by', 'checked_by_username',
            'total_logs_checked', 'corrupted_logs', 'result', 'details'
        ]
        read_only_fields = ['check_id', 'checked_at']
