"""monitoring/api_views.py – DRF ViewSets for monitoring models."""

from rest_framework import serializers, viewsets, permissions

from .models import HealthcareSystem, MonitoringEvent


class HealthcareSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthcareSystem
        fields = '__all__'


class MonitoringEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringEvent
        fields = '__all__'


class HealthcareSystemViewSet(viewsets.ModelViewSet):
    queryset = HealthcareSystem.objects.all()
    serializer_class = HealthcareSystemSerializer
    permission_classes = [permissions.IsAuthenticated]


class MonitoringEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonitoringEvent.objects.select_related('system').order_by('-occurred_at')
    serializer_class = MonitoringEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['severity', 'event_type', 'is_reviewed']
