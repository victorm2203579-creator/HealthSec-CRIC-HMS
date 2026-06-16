"""reports/api_views.py – DRF ViewSets for generated reports."""

from rest_framework import serializers, viewsets, permissions
from .models import GeneratedReport


class GeneratedReportSerializer(serializers.ModelSerializer):
    generated_by_username = serializers.CharField(
        source='generated_by.username', read_only=True
    )

    class Meta:
        model = GeneratedReport
        fields = '__all__'
        read_only_fields = ['generated_at', 'generated_by']


class GeneratedReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GeneratedReport.objects.select_related('generated_by').order_by('-generated_at')
    serializer_class = GeneratedReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['report_type']
