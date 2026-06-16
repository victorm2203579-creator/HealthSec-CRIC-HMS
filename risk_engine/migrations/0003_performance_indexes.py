"""
Performance indexes on risk engine high-traffic fields.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk_engine', '0002_vulnerabilityrecord_threatfeed_riskassessment_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='threatevent',
            index=models.Index(fields=['severity', 'status'], name='re_threat_sev_status_idx'),
        ),
        migrations.AddIndex(
            model_name='threatevent',
            index=models.Index(fields=['detected_at'], name='re_threat_detected_idx'),
        ),
        migrations.AddIndex(
            model_name='vulnerabilityrecord',
            index=models.Index(fields=['severity', 'patched'], name='re_vuln_sev_patch_idx'),
        ),
        migrations.AddIndex(
            model_name='vulnerabilityrecord',
            index=models.Index(fields=['discovered_at'], name='re_vuln_discovered_idx'),
        ),
    ]
