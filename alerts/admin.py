"""alerts/admin.py – Admin registrations for alerts and incidents."""

from django.contrib import admin
from .models import Alert, Incident, AlertRule


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'status', 'alert_type', 'affected_system', 'assigned_to', 'is_read', 'created_at')
    list_filter = ('severity', 'status', 'alert_type', 'is_read', 'created_at')
    search_fields = ('title', 'description', 'tags')
    date_hierarchy = 'created_at'
    raw_id_fields = ('assigned_to', 'affected_system', 'source_event', 'acknowledged_by', 'resolved_by')
    readonly_fields = ('id', 'created_at', 'updated_at', 'read_at', 'acknowledged_at', 'resolved_at')
    fieldsets = (
        ('Alert Information', {
            'fields': ('id', 'title', 'description', 'alert_type', 'severity', 'tags')
        }),
        ('Status & Workflow', {
            'fields': ('status', 'is_read', 'read_at')
        }),
        ('Acknowledgement', {
            'fields': ('acknowledged_at', 'acknowledged_by'),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('resolved_at', 'resolved_by'),
            'classes': ('collapse',)
        }),
        ('Assignment & Context', {
            'fields': ('assigned_to', 'affected_system', 'source_event')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_number', 'title', 'phase', 'incident_commander', 'detected_at', 'closed_at')
    list_filter = ('phase', 'detected_at', 'closed_at')
    search_fields = ('incident_number', 'title', 'description')
    filter_horizontal = ('alerts',)
    raw_id_fields = ('incident_commander', 'created_by')
    readonly_fields = ('id', 'incident_number', 'incident_sequence', 'created_at', 'updated_at', 'timeline')
    date_hierarchy = 'detected_at'
    fieldsets = (
        ('Incident Identification', {
            'fields': ('id', 'incident_number', 'incident_sequence', 'title', 'description')
        }),
        ('Timeline & Status', {
            'fields': ('phase', 'detected_at', 'contained_at', 'resolved_at', 'closed_at')
        }),
        ('Response Team', {
            'fields': ('incident_commander', 'created_by')
        }),
        ('Related Alerts', {
            'fields': ('alerts',)
        }),
        ('Assessment & Analysis', {
            'fields': ('impact_assessment', 'root_cause', 'lessons_learned', 'remediation_steps'),
            'classes': ('collapse',)
        }),
        ('Timeline Log', {
            'fields': ('timeline',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'alert_type', 'severity', 'is_active', 'created_at')
    list_filter = ('rule_type', 'alert_type', 'severity', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('created_by',)
    fieldsets = (
        ('Rule Information', {
            'fields': ('id', 'name', 'description', 'rule_type', 'is_active')
        }),
        ('Alert Configuration', {
            'fields': ('alert_type', 'severity')
        }),
        ('Rule Logic', {
            'fields': ('conditions', 'actions')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
