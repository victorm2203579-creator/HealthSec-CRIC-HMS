"""alerts/api_views.py – DRF ViewSets for alerts and incidents."""

from rest_framework import serializers, viewsets, permissions
from .models import Alert, Incident


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.select_related('affected_system').order_by('-created_at')
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['severity', 'status', 'alert_type', 'is_read']


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.order_by('-detected_at')
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['phase']
