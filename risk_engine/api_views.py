"""risk_engine/api_views.py – DRF ViewSets for risk engine models."""

from django.utils import timezone
from rest_framework import serializers, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .engine import RiskIntelligenceEngine
from .models import RiskScore, ThreatEvent, Vulnerability

_engine = RiskIntelligenceEngine()


class RiskScoreSerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(source='system.name', read_only=True)

    class Meta:
        model = RiskScore
        fields = ['id', 'system', 'system_name', 'score', 'risk_level',
                  'threat_likelihood', 'impact_magnitude', 'vulnerability_index',
                  'control_effectiveness', 'rationale', 'computed_at']
        read_only_fields = ['id', 'computed_at']


class VulnerabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vulnerability
        fields = '__all__'


class RiskScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RiskScore.objects.select_related('system').order_by('-computed_at')
    serializer_class = RiskScoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['risk_level', 'system']


class VulnerabilityViewSet(viewsets.ModelViewSet):
    queryset = Vulnerability.objects.all()
    serializer_class = VulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'cve_id']


class CurrentRiskScoreView(APIView):
    """
    GET /api/risk/current-score/

    Returns the live overall risk score calculated from open and investigating
    ThreatEvent records.  No authentication exemption — requires login.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        open_events = ThreatEvent.objects.filter(
            status__in=[ThreatEvent.Status.OPEN, ThreatEvent.Status.INVESTIGATING]
        )
        score = _engine.calculate_risk_score(open_events)
        level = _engine.classify_risk_level(score)
        return Response({
            'score': round(score, 1),
            'level': level,
            'threat_count': open_events.count(),
            'last_updated': timezone.now().isoformat(),
        })
