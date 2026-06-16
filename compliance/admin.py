"""compliance/admin.py – Admin registrations for compliance models."""

from django.contrib import admin
from .models import (
    ComplianceCheckResult,
    ComplianceControl,
    ComplianceEvidence,
    ComplianceFramework,
    ComplianceReport,
    Control,
    ControlAssessment,
)


# ---------------------------------------------------------------------------
# Framework
# ---------------------------------------------------------------------------

@admin.register(ComplianceFramework)
class ComplianceFrameworkAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name', 'version', 'applicable_region', 'issuing_body', 'is_active')
    list_filter  = ('is_active', 'applicable_region')
    search_fields = ('name', 'short_name', 'issuing_body')
    readonly_fields = ('framework_id', 'created_at')


# ---------------------------------------------------------------------------
# Legacy models
# ---------------------------------------------------------------------------

@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display  = ('control_id', 'title', 'framework', 'category', 'is_mandatory')
    list_filter   = ('framework', 'category', 'is_mandatory')
    search_fields = ('control_id', 'title')


class ComplianceEvidenceInline(admin.TabularInline):
    model = ComplianceEvidence
    extra = 0


@admin.register(ControlAssessment)
class ControlAssessmentAdmin(admin.ModelAdmin):
    list_display = ('control', 'status', 'score', 'assessed_by', 'assessed_at')
    list_filter  = ('status',)
    inlines      = [ComplianceEvidenceInline]
    date_hierarchy = 'assessed_at'


# ---------------------------------------------------------------------------
# New engine models
# ---------------------------------------------------------------------------

@admin.register(ComplianceControl)
class ComplianceControlAdmin(admin.ModelAdmin):
    list_display  = ('control_code', 'title', 'framework', 'control_category',
                     'weight', 'automated_check', 'check_function_name')
    list_filter   = ('framework', 'control_category', 'automated_check')
    search_fields = ('control_code', 'title', 'description')
    readonly_fields = ('control_id',)


class ComplianceCheckResultInline(admin.TabularInline):
    model = ComplianceCheckResult
    extra = 0
    readonly_fields = ('result_id', 'checked_at', 'status', 'score', 'checked_by')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ComplianceCheckResult)
class ComplianceCheckResultAdmin(admin.ModelAdmin):
    list_display   = ('control', 'status', 'score', 'checked_by', 'checked_at', 'due_date')
    list_filter    = ('status', 'control__framework')
    search_fields  = ('control__control_code', 'notes', 'evidence')
    date_hierarchy = 'checked_at'
    readonly_fields = ('result_id', 'checked_at')

    def has_add_permission(self, request):
        return False


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display   = ('framework', 'compliance_level', 'overall_score',
                      'passed_controls', 'failed_controls', 'generated_by', 'generated_at')
    list_filter    = ('framework', 'compliance_level')
    date_hierarchy = 'generated_at'
    readonly_fields = ('report_id', 'generated_at')
