"""compliance/api_views.py – DRF ViewSets for compliance models."""

from rest_framework import serializers, viewsets, permissions
from .models import ComplianceFramework, Control, ControlAssessment


class ComplianceFrameworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceFramework
        fields = '__all__'


class ControlSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source='framework.short_name', read_only=True)

    class Meta:
        model = Control
        fields = '__all__'


class ControlAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlAssessment
        fields = '__all__'


class ComplianceFrameworkViewSet(viewsets.ModelViewSet):
    queryset = ComplianceFramework.objects.filter(is_active=True)
    serializer_class = ComplianceFrameworkSerializer
    permission_classes = [permissions.IsAuthenticated]


class ControlViewSet(viewsets.ModelViewSet):
    queryset = Control.objects.select_related('framework')
    serializer_class = ControlSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['framework', 'category', 'is_mandatory']


class ControlAssessmentViewSet(viewsets.ModelViewSet):
    queryset = ControlAssessment.objects.select_related('control', 'assessed_by')
    serializer_class = ControlAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'control__framework']
