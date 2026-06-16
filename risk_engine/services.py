"""
risk_engine/services.py
=======================
Business logic for computing risk scores.

The scoring algorithm is a simplified CVSS-inspired model:

  residual_risk = threat_likelihood × impact_magnitude × (1 - control_effectiveness)
  raw_score     = residual_risk + vulnerability_index
  final_score   = min(raw_score, 10.0)

All component values are normalised to the [0, 1] range before multiplication
and the result is scaled back to [0, 10].

This module intentionally avoids ML for the core score to keep it
explainable and auditable.  scikit-learn is used in anomaly_detection.py
for supplementary outlier detection on event streams.
"""

import logging
from decimal import Decimal

from django.utils import timezone

from monitoring.models import HealthcareSystem, MonitoringEvent
from .models import RiskScore, Vulnerability

logger = logging.getLogger('healthsec.risk_engine')


class RiskScoringService:
    """Compute and persist a risk score for a given HealthcareSystem."""

    def compute(self, system: HealthcareSystem, user=None) -> RiskScore:
        """
        Calculate the current risk score for `system` and save it to the database.
        Returns the saved RiskScore instance.
        """
        inputs = self._gather_inputs(system)
        components = self._calculate_components(inputs)
        raw_score = self._aggregate(components)
        score = min(Decimal(str(round(raw_score, 2))), Decimal('10.00'))

        risk_score = RiskScore.objects.create(
            system=system,
            score=score,
            risk_level=RiskScore.classify(float(score)),
            threat_likelihood=Decimal(str(round(components['threat_likelihood'], 2))),
            impact_magnitude=Decimal(str(round(components['impact_magnitude'], 2))),
            vulnerability_index=Decimal(str(round(components['vulnerability_index'], 2))),
            control_effectiveness=Decimal(str(round(components['control_effectiveness'], 2))),
            rationale=self._build_rationale(components, inputs),
            calculation_inputs=inputs,
            computed_by=user,
        )

        logger.info('Risk score computed for %s: %s (%s)', system.name, score, risk_score.risk_level)
        return risk_score

    # --- Private helpers --------------------------------------------------- #

    def _gather_inputs(self, system: HealthcareSystem) -> dict:
        """Collect raw data points from related models."""
        recent_critical = MonitoringEvent.objects.filter(
            system=system,
            severity=MonitoringEvent.Severity.CRITICAL,
        ).count()

        recent_high = MonitoringEvent.objects.filter(
            system=system,
            severity=MonitoringEvent.Severity.HIGH,
        ).count()

        open_vulns = Vulnerability.objects.filter(
            affected_systems=system,
            status=Vulnerability.VulnStatus.OPEN,
        )
        avg_cvss = (
            open_vulns.exclude(cvss_score=None)
            .values_list('cvss_score', flat=True)
        )
        avg_cvss_score = (sum(float(s) for s in avg_cvss) / len(avg_cvss)) if avg_cvss else 0

        return {
            'contains_phi': system.contains_phi,
            'system_status': system.status,
            'critical_events': recent_critical,
            'high_events': recent_high,
            'open_vulnerabilities': open_vulns.count(),
            'avg_cvss': avg_cvss_score,
            'data_assets': system.data_assets.count(),
            'phi_assets': system.data_assets.filter(
                classification__in=['PHI', 'PII']
            ).count(),
        }

    def _calculate_components(self, inputs: dict) -> dict:
        """Normalise raw inputs into 0–10 component scores."""
        # Threat likelihood: driven by open critical/high events
        threat = min((inputs['critical_events'] * 2 + inputs['high_events']) / 10.0, 1.0) * 10

        # Impact magnitude: PHI systems and many data assets = higher impact
        impact = 5.0
        if inputs['contains_phi']:
            impact += 2.0
        impact += min(inputs['phi_assets'] * 0.5, 2.0)
        impact = min(impact, 10.0)

        # Vulnerability index: average CVSS of open vulns
        vuln_index = min(inputs['avg_cvss'], 10.0)

        # Control effectiveness: placeholder – would pull from compliance scores
        control = 5.0  # Assume 50% baseline control maturity

        return {
            'threat_likelihood': round(threat, 2),
            'impact_magnitude': round(impact, 2),
            'vulnerability_index': round(vuln_index, 2),
            'control_effectiveness': round(control, 2),
        }

    def _aggregate(self, components: dict) -> float:
        """Combine components into a single 0–10 score."""
        tl = components['threat_likelihood'] / 10.0
        im = components['impact_magnitude'] / 10.0
        vi = components['vulnerability_index'] / 10.0
        ce = components['control_effectiveness'] / 10.0

        residual = tl * im * (1 - ce)
        return (residual + vi) * 10 / 2  # average the two primary signals

    def _build_rationale(self, components: dict, inputs: dict) -> str:
        """Produce a human-readable explanation of the score."""
        lines = [
            f"Threat Likelihood: {components['threat_likelihood']}/10 "
            f"(based on {inputs['critical_events']} critical and {inputs['high_events']} high events)",
            f"Impact Magnitude: {components['impact_magnitude']}/10 "
            f"({'PHI system' if inputs['contains_phi'] else 'non-PHI system'}, "
            f"{inputs['phi_assets']} PHI/PII assets)",
            f"Vulnerability Index: {components['vulnerability_index']}/10 "
            f"({inputs['open_vulnerabilities']} open vulnerabilities, avg CVSS {inputs['avg_cvss']:.1f})",
            f"Control Effectiveness: {components['control_effectiveness']}/10 (baseline estimate)",
        ]
        return '\n'.join(lines)
