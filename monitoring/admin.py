"""monitoring/admin.py – Admin registrations for monitoring models."""

from django.contrib import admin
from .models import (
    DataAsset,
    HealthcareSystem,
    MonitoringEvent,
    PatientRecord,
    RecordAccessLog,
    SuspiciousActivity,
)


@admin.register(HealthcareSystem)
class HealthcareSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'system_type', 'status', 'contains_phi', 'ip_address')
    list_filter = ('system_type', 'status', 'contains_phi')
    search_fields = ('name', 'vendor', 'hostname', 'ip_address')


@admin.register(MonitoringEvent)
class MonitoringEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'system', 'event_type', 'severity', 'occurred_at', 'is_reviewed')
    list_filter = ('severity', 'event_type', 'is_reviewed')
    search_fields = ('title', 'description')
    date_hierarchy = 'occurred_at'


@admin.register(DataAsset)
class DataAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'system', 'classification', 'record_count', 'encrypted_at_rest')
    list_filter = ('classification', 'encrypted_at_rest')


@admin.register(PatientRecord)
class PatientRecordAdmin(admin.ModelAdmin):
    """Admin for simulated patient records."""
    list_display = (
        'patient_code', 'record_type', 'sensitivity_level',
        'department', 'is_flagged', 'created_at',
    )
    list_filter = ('record_type', 'sensitivity_level', 'is_flagged', 'department')
    search_fields = ('patient_code', 'department')
    readonly_fields = ('record_id', 'created_at', 'last_modified')
    date_hierarchy = 'created_at'


@admin.register(RecordAccessLog)
class RecordAccessLogAdmin(admin.ModelAdmin):
    """Read-only admin for record access logs (append-only audit trail)."""
    list_display = (
        'timestamp', 'user', 'patient_record', 'access_type',
        'access_hour', 'is_suspicious', 'ip_address',
    )
    list_filter = ('access_type', 'is_suspicious')
    search_fields = ('user__username', 'patient_record__patient_code', 'ip_address')
    readonly_fields = tuple(f.name for f in RecordAccessLog._meta.get_fields()
                            if hasattr(f, 'name'))
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SuspiciousActivity)
class SuspiciousActivityAdmin(admin.ModelAdmin):
    """Admin for suspicious activity records with resolve action."""
    list_display = (
        'timestamp', 'user', 'activity_type', 'severity',
        'related_record', 'resolved', 'resolved_by',
    )
    list_filter = ('activity_type', 'severity', 'resolved')
    search_fields = ('user__username', 'description')
    readonly_fields = ('activity_id', 'timestamp')
    date_hierarchy = 'timestamp'
    actions = ['mark_resolved']

    @admin.action(description='Mark selected activities as resolved')
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(resolved=False).update(
            resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now(),
        )
        self.message_user(request, f'{updated} activity/activities marked as resolved.')
