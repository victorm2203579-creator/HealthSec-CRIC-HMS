"""reports/admin.py – Admin registrations for generated reports."""

from django.contrib import admin
from .models import GeneratedReport


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'generated_by', 'generated_at')
    list_filter = ('report_type',)
    date_hierarchy = 'generated_at'
    readonly_fields = ('generated_at',)
