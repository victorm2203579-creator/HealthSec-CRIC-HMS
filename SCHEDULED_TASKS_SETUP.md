# Scheduled Tasks Setup Guide — HealthSec

## Overview

HealthSec includes automated scheduled tasks that run on a fixed schedule:
- Run compliance checks every 24 hours
- Run anomaly detection scan every 6 hours
- Send daily threat summary email every morning
- Clean up old session data weekly

This guide covers setup using both **django-crontab** (simpler) and **Celery Beat** (more powerful).

---

## Option 1: Django-Crontab (Simpler)

### Installation

```bash
pip install django-crontab
```

### Configuration (settings.py)

Add to installed apps:

```python
INSTALLED_APPS = [
    # ... other apps ...
    'django_crontab',
]

# Crontab schedule configuration
CRONJOBS = [
    # Run compliance checks daily at 2:00 AM
    ('0 2 * * *', 'compliance.management.commands.run_compliance_checks', '>> /var/log/healthsec/cron.log 2>&1'),

    # Run anomaly detection scan every 6 hours
    ('0 */6 * * *', 'risk_engine.management.commands.run_anomaly_scan', '>> /var/log/healthsec/cron.log 2>&1'),

    # Send threat summary email daily at 9:00 AM
    ('0 9 * * *', 'alerts.management.commands.send_threat_summary', '>> /var/log/healthsec/cron.log 2>&1'),

    # Clean up expired sessions weekly (Sunday at 3:00 AM)
    ('0 3 * * 0', 'accounts.management.commands.cleanup_sessions', '>> /var/log/healthsec/cron.log 2>&1'),
]

# Timezone for cron schedules
CRONTAB_TIMEZONE = 'Africa/Lagos'  # or your timezone

# Command timeout (seconds)
CRONTAB_COMMAND_TIMEOUT = 300  # 5 minutes
```

### Installation & Management

```bash
# Install cron jobs
python manage.py crontab add

# View installed cron jobs
python manage.py crontab show

# Remove cron jobs
python manage.py crontab remove

# View log file
tail -f /var/log/healthsec/cron.log
```

### Manual Test

```bash
# Test compliance check command
python manage.py run_compliance_checks --verbose

# Test anomaly scan
python manage.py run_anomaly_scan --days 7 --verbose

# Test threat summary
python manage.py send_threat_summary --verbose

# Test session cleanup
python manage.py cleanup_sessions --verbose
```

---

## Option 2: Celery + Celery Beat (Recommended for Production)

### Installation

```bash
pip install celery celery-beat redis
```

### Celery Configuration (healthsec/celery.py)

```python
"""
healthsec/celery.py
==================
Celery configuration for HealthSec.
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsec.settings')

app = Celery('healthsec')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Request: {self.request!r}')


# Celery Beat scheduled tasks
app.conf.beat_schedule = {
    'run-compliance-checks': {
        'task': 'compliance.tasks.run_compliance_checks_task',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
    },
    'run-anomaly-scan': {
        'task': 'risk_engine.tasks.run_anomaly_scan_task',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'send-threat-summary': {
        'task': 'alerts.tasks.send_threat_summary_task',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
    },
    'cleanup-sessions': {
        'task': 'accounts.tasks.cleanup_sessions_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM
    },
}

# Celery settings
app.conf.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='Africa/Lagos',
    CELERY_ENABLE_UTC=True,
    CELERY_TASK_TRACK_STARTED=True,
    CELERY_TASK_TIME_LIMIT=30 * 60,  # 30 minutes hard limit
)
```

### Django Settings Configuration

Add to `healthsec/settings.py`:

```python
# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Lagos'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True

# Logging for Celery
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/celery.log',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['celery'],
            'level': 'DEBUG',
        },
    },
}
```

### Create Celery Tasks

Create `compliance/tasks.py`:

```python
from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_compliance_checks_task():
    """Celery task for running compliance checks."""
    logger.info("Running compliance checks via Celery")
    call_command('run_compliance_checks', verbose=True)
```

Similarly create `risk_engine/tasks.py`, `alerts/tasks.py`, `accounts/tasks.py`.

### Running Celery

```bash
# Start Celery worker
celery -A healthsec worker --loglevel=info

# Start Celery Beat scheduler (in separate terminal)
celery -A healthsec beat --loglevel=info

# OR run both in one process (development)
celery -A healthsec worker --beat --loglevel=info

# Monitor tasks
celery -A healthsec events
```

### Docker Compose for Development

```yaml
version: '3'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  celery_worker:
    build: .
    command: celery -A healthsec worker --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  celery_beat:
    build: .
    command: celery -A healthsec beat --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
```

---

## Cron Schedule Reference

### Cron Expression Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

### Common Schedules

```
0 2 * * *     → 2:00 AM every day
0 */6 * * *   → Every 6 hours
0 9 * * *     → 9:00 AM every day
0 3 * * 0     → 3:00 AM every Sunday
0 0 1 * *     → Midnight on 1st of month
*/30 * * * *  → Every 30 minutes
```

---

## Monitoring & Debugging

### Django-Crontab

```bash
# Check cron log
tail -f /var/log/healthsec/cron.log

# Manual test
python manage.py run_compliance_checks --verbose
```

### Celery Beat

```bash
# View scheduled tasks
celery -A healthsec inspect scheduled

# View active tasks
celery -A healthsec inspect active

# View task stats
celery -A healthsec inspect stats

# View worker nodes
celery -A healthsec inspect active_queues

# Purge pending tasks (BE CAREFUL)
celery -A healthsec purge
```

### Logs Location

```
/var/log/healthsec/cron.log       # Django-crontab
logs/celery.log                     # Celery task logs
logs/celery_beat.log                # Celery Beat scheduler logs
```

---

## Task Specifications

### 1. Run Compliance Checks

**Schedule**: Every 24 hours at 2:00 AM  
**Command**: `python manage.py run_compliance_checks`  
**Output**: Runs all automated compliance checks across active frameworks  
**Time**: ~5 minutes  

### 2. Run Anomaly Detection Scan

**Schedule**: Every 6 hours  
**Command**: `python manage.py run_anomaly_scan --days 7`  
**Output**: Analyzes recent access logs, creates SuspiciousActivity records  
**Time**: ~10 minutes  

### 3. Send Threat Summary Email

**Schedule**: Daily at 9:00 AM  
**Command**: `python manage.py send_threat_summary`  
**Output**: Sends email to all admins with threat summary  
**Time**: ~2 minutes  

### 4. Clean Up Sessions

**Schedule**: Weekly (Sundays) at 3:00 AM  
**Command**: `python manage.py cleanup_sessions --days 30`  
**Output**: Deletes sessions older than 30 days  
**Time**: ~1 minute  

---

## Production Deployment

### Using Systemd (Linux)

Create `/etc/systemd/system/healthsec-celery.service`:

```ini
[Unit]
Description=HealthSec Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=healthsec
Group=healthsec
WorkingDirectory=/opt/healthsec
ExecStart=/opt/healthsec/venv/bin/celery -A healthsec worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/healthsec-beat.service`:

```ini
[Unit]
Description=HealthSec Celery Beat
After=network.target redis.service healthsec-celery.service

[Service]
Type=simple
User=healthsec
Group=healthsec
WorkingDirectory=/opt/healthsec
ExecStart=/opt/healthsec/venv/bin/celery -A healthsec beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
sudo systemctl enable healthsec-celery
sudo systemctl enable healthsec-beat
sudo systemctl start healthsec-celery
sudo systemctl start healthsec-beat

# View logs
sudo journalctl -u healthsec-celery -f
sudo journalctl -u healthsec-beat -f
```

---

## Troubleshooting

### Task Not Running

```bash
# Check if cron is installed (django-crontab)
crontab -l

# Check if Redis is running (Celery)
redis-cli ping  # Should return PONG

# Check Celery worker status
celery -A healthsec inspect active
```

### Database Lock Issues

If tasks fail with database lock errors:

```python
# In task, use connection retry
from django.db import connections
connections.close_all()

# Or run in transaction
from django.db import transaction
@transaction.atomic
def my_task():
    pass
```

### Time Zone Issues

```python
# Ensure timezone is set in settings
CELERY_TIMEZONE = 'Africa/Lagos'

# Verify task time in logs
import logging
logger.info(f"Task running at {timezone.now()}")
```

---

## Best Practices

✓ **Do:**
- Use Celery for production (more reliable)
- Monitor task execution with logs
- Set reasonable timeouts (CELERY_TASK_TIME_LIMIT)
- Run worker and beat in separate processes
- Use Redis for broker (not RabbitMQ for small deployments)
- Schedule checks during low-traffic hours

✗ **Don't:**
- Run heavy tasks synchronously in HTTP requests
- Skip error handling in tasks
- Ignore failed task notifications
- Use default settings for production
- Run Celery with high worker concurrency on small machines

---

## Testing Tasks

```bash
# Test compliance check
python manage.py run_compliance_checks --verbose

# Test anomaly scan (last 1 day)
python manage.py run_anomaly_scan --days 1 --verbose

# Test threat summary
python manage.py send_threat_summary --verbose

# Test session cleanup
python manage.py cleanup_sessions --verbose
```

---

**Last Updated**: 2026-05-25  
**Version**: 1.0  
**Status**: Ready for Production Deployment
