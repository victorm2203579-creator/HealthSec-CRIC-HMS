"""risk_engine/admin.py – Admin registrations for risk engine models."""

from django.contrib import admin
from .models import (
    RiskAssessment,
    RiskScore,
    ThreatEvent,
    ThreatFeed,
    ThreatIntelFeed,
    Vulnerability,
    VulnerabilityRecord,
)


@admin.register(RiskScore)
class RiskScoreAdmin(admin.ModelAdmin):
    list_display = ('system', 'score', 'risk_level', 'computed_at', 'computed_by')
    list_filter = ('risk_level',)
    date_hierarchy = 'computed_at'
    readonly_fields = ('computed_at',)


@admin.register(Vulnerability)
class VulnerabilityAdmin(admin.ModelAdmin):
    list_display = ('title', 'cve_id', 'cvss_score', 'status', 'remediation_due')
    list_filter = ('status',)
    search_fields = ('title', 'cve_id', 'description')
    filter_horizontal = ('affected_systems',)


@admin.register(ThreatIntelFeed)
class ThreatIntelFeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'feed_type', 'source', 'relevance_score', 'published_at', 'is_actioned')
    list_filter = ('feed_type', 'is_actioned')
    search_fields = ('title', 'source')


@admin.register(ThreatEvent)
class ThreatEventAdmin(admin.ModelAdmin):
    list_display = ('threat_id', 'threat_type', 'severity', 'status', 'detected_at', 'target_user', 'assigned_to')
    list_filter = ('threat_type', 'severity', 'status')
    search_fields = ('description', 'source_ip', 'target_resource')
    date_hierarchy = 'detected_at'
    readonly_fields = ('threat_id', 'detected_at')
    raw_id_fields = ('target_user', 'assigned_to')


@admin.register(VulnerabilityRecord)
class VulnerabilityRecordAdmin(admin.ModelAdmin):
    list_display = ('title', 'cve_reference', 'cvss_score', 'severity', 'patched', 'discovered_at')
    list_filter = ('severity', 'patched')
    search_fields = ('title', 'cve_reference', 'description', 'affected_component')
    readonly_fields = ('vuln_id',)


@admin.register(ThreatFeed)
class ThreatFeedAdmin(admin.ModelAdmin):
    list_display = ('threat_indicator', 'indicator_type', 'feed_name', 'confidence_score', 'is_active', 'added_at')
    list_filter = ('indicator_type', 'is_active')
    search_fields = ('threat_indicator', 'feed_name', 'threat_category')


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ('assessment_id', 'risk_level', 'overall_risk_score', 'conducted_by', 'conducted_at', 'next_assessment_due')
    list_filter = ('risk_level',)
    date_hierarchy = 'conducted_at'
    readonly_fields = ('assessment_id', 'conducted_at')
