"""
Performance indexes on alerts high-traffic fields.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0002_alertrule_alert_acknowledged_at_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='alert',
            index=models.Index(fields=['severity', 'status'], name='al_alert_sev_status_idx'),
        ),
        migrations.AddIndex(
            model_name='alert',
            index=models.Index(fields=['created_at'], name='al_alert_created_idx'),
        ),
        migrations.AddIndex(
            model_name='alert',
            index=models.Index(fields=['is_read', 'status'], name='al_alert_read_status_idx'),
        ),
    ]
