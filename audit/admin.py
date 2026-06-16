"""
audit/admin.py
==============
Read-only admin interface for audit logs. The audit log is append-only:
no edits, additions, or deletions are permitted through the admin.
"""

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import AuditLog, AuditLogIntegrityCheck


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Append-only admin interface for audit logs.

    - No adding new logs (they're created programmatically)
    - No editing existing logs (immutable)
    - No deleting logs (prevents tampering)
    """

    list_display = (
        'timestamp', 'user', 'action', 'action_category',
        'status', 'ip_address', 'checksum_preview'
    )
    list_filter = ('action_category', 'status', 'timestamp')
    search_fields = ('action', 'description', 'user__username', 'ip_address', 'target_model')
    date_hierarchy = 'timestamp'
    readonly_fields = (
        'log_id', 'user', 'action_category', 'action', 'description',
        'target_model', 'target_id', 'old_value', 'new_value',
        'ip_address', 'user_agent', 'session_key', 'timestamp', 'status', 'checksum'
    )

    fieldsets = (
        ('Log Identification', {
            'fields': ('log_id', 'timestamp')
        }),
        ('Action Details', {
            'fields': ('user', 'action_category', 'action', 'description', 'status')
        }),
        ('Target Information', {
            'fields': ('target_model', 'target_id'),
            'classes': ('collapse',)
        }),
        ('Change Data', {
            'fields': ('old_value', 'new_value'),
            'classes': ('collapse',)
        }),
        ('HTTP Context', {
            'fields': ('ip_address', 'user_agent', 'session_key'),
            'classes': ('collapse',)
        }),
        ('Integrity', {
            'fields': ('checksum',),
            'classes': ('collapse',)
        }),
    )

    def checksum_preview(self, obj):
        """Display first 16 characters of checksum."""
        return obj.checksum[:16] + '...' if obj.checksum else '—'

    checksum_preview.short_description = 'Checksum (preview)'

    def has_add_permission(self, request):
        """Prevent manual log creation - logs are created programmatically."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing of audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs - the log is immutable and append-only."""
        return False

    def delete_model(self, request, obj):
        """Override delete to raise PermissionDenied."""
        raise PermissionDenied(
            'Audit logs are immutable and cannot be deleted. '
            'This is a security requirement for compliance.'
        )

    def delete_queryset(self, request, queryset):
        """Override bulk delete to raise PermissionDenied."""
        raise PermissionDenied(
            'Audit logs are immutable and cannot be deleted. '
            'This is a security requirement for compliance.'
        )


@admin.register(AuditLogIntegrityCheck)
class AuditLogIntegrityCheckAdmin(admin.ModelAdmin):
    """Read-only admin interface for integrity check results."""

    list_display = (
        'checked_at', 'checked_by', 'result', 'total_logs_checked',
        'corrupted_logs', 'integrity_status'
    )
    list_filter = ('result', 'checked_at')
    search_fields = ('checked_by__username',)
    date_hierarchy = 'checked_at'
    readonly_fields = (
        'check_id', 'checked_at', 'checked_by', 'total_logs_checked',
        'corrupted_logs', 'result', 'details'
    )

    fieldsets = (
        ('Check Information', {
            'fields': ('check_id', 'checked_at', 'checked_by')
        }),
        ('Results', {
            'fields': ('result', 'total_logs_checked', 'corrupted_logs')
        }),
        ('Details', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )

    def integrity_status(self, obj):
        """Display status icon."""
        if obj.result == AuditLogIntegrityCheck.Result.INTACT:
            return '✓ Intact'
        elif obj.result == AuditLogIntegrityCheck.Result.TAMPERED:
            return '✗ Tampered'
        else:
            return '⚠ Error'

    integrity_status.short_description = 'Status'

    def has_add_permission(self, request):
        """Prevent manual check creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing of check results."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of check records."""
        return False
