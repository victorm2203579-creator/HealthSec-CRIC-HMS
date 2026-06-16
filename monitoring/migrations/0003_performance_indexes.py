"""
Performance indexes on high-traffic monitoring fields.
Speeds up dashboard queries, access log filtering, and suspicious activity lookups.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0002_patientrecord_suspiciousactivity_recordaccesslog_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='recordaccesslog',
            index=models.Index(fields=['timestamp'], name='mon_ral_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='recordaccesslog',
            index=models.Index(fields=['user', 'is_suspicious'], name='mon_ral_user_susp_idx'),
        ),
        migrations.AddIndex(
            model_name='recordaccesslog',
            index=models.Index(fields=['access_hour'], name='mon_ral_hour_idx'),
        ),
        migrations.AddIndex(
            model_name='monitoringevent',
            index=models.Index(fields=['occurred_at', 'severity'], name='mon_event_occ_sev_idx'),
        ),
        migrations.AddIndex(
            model_name='suspiciousactivity',
            index=models.Index(fields=['timestamp', 'resolved'], name='mon_susp_ts_res_idx'),
        ),
    ]
