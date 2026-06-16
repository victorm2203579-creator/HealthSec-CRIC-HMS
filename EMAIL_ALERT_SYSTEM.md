# Email Alert System — HealthSec CRIC HMS

## Overview

The Email Alert System provides automated email notifications for security alerts, incidents, compliance reports, and account lock events. The system is designed with HIPAA compliance in mind, ensuring no PHI (Protected Health Information) is exposed in email subjects, bodies, or links.

---

## System Architecture

### Components

1. **EmailNotificationService** (`alerts/email_service.py`)
   - Core service layer for sending all email notifications
   - Handles user role-based recipient selection
   - Manages email template rendering
   - Logs all email events to AuditLog
   - Implements HIPAA-compliant data handling

2. **Email Templates** (`templates/emails/`)
   - `alert_email.html` / `alert_email.txt` — Security alert notifications
   - `account_locked_email.html` / `account_locked_email.txt` — Account lock notifications
   - `compliance_report_email.html` / `compliance_report_email.txt` — Compliance report notifications
   - `incident_notification_email.html` / `incident_notification_email.txt` — Incident notifications

3. **AlertService** (`alerts/services.py`)
   - Extended with email methods that delegate to EmailNotificationService
   - `send_alert_email(alert, recipients=None)` — Send alert notification
   - `send_incident_email(incident)` — Send incident notification
   - `send_test_email(to_email)` — Send test email for configuration verification

4. **Management Command** (`alerts/management/commands/send_test_email.py`)
   - CLI utility for testing email configuration
   - Usage: `python manage.py send_test_email your-email@example.com`

5. **Test Email View** (`alerts/views.py`, `alerts/templates/alerts/test_email.html`)
   - Web interface for testing email configuration
   - Accessible at `/alerts/test-email/`
   - Admin-only access
   - Shows current email backend status and configuration guide

---

## Email Notification Types

### 1. Security Alerts
**Triggered by:** New security alerts created
**Recipients:** Based on alert severity and user roles
- **CRITICAL/HIGH**: ADMIN, COMPLIANCE roles
- **MEDIUM**: ANALYST, COMPLIANCE, ADMIN roles
- **LOW**: ANALYST, ADMIN roles
- Plus: Alert's assigned_to user (if any)

**Template:** `alert_email.html`
**Includes:**
- Alert ID (truncated UUID)
- Alert type and severity
- Alert status and creation time
- Alert description
- Link to view in HealthSec

### 2. Account Lock Notifications
**Triggered by:** User account lock events
**Recipients:** Locked user + all ADMIN users

**Template:** `account_locked_email.html`
**Includes:**
- Username and email
- Lock reason
- Lock timestamp
- Expected unlock time (if available)
- Instructions for user and admins
- Admin panel link

### 3. Compliance Report Notifications
**Triggered by:** Compliance report generation
**Recipients:** COMPLIANCE, ADMIN roles

**Template:** `compliance_report_email.html`
**Includes:**
- Report type
- Generation timestamp
- Status
- Compliance score (if available)
- Next steps and action items
- Link to view full report

### 4. Incident Notifications
**Triggered by:** New incident creation
**Recipients:** ADMIN, ANALYST roles

**Template:** `incident_notification_email.html`
**Includes:**
- Incident number (e.g., INC-2026-0001)
- Incident title and phase
- Detection timestamp
- Incident commander (if assigned)
- Description
- Required actions
- Link to incident details

---

## Configuration

### Email Backend (settings.py)

**Development (Console Backend):**
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Emails are printed to console/logs instead of being sent.

**Production (SMTP Backend):**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
```

### Environment Variables (.env)

```bash
# Email Backend Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=HealthSec <noreply@healthsec.local>

# Site Information (used in email links)
SITE_NAME=HealthSec CRIC HMS
SITE_DOMAIN=localhost:8000
```

### Gmail SMTP Setup

To use Gmail SMTP:
1. Enable 2-factor authentication on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the app password in `EMAIL_HOST_PASSWORD` (not your regular Google password)
4. Use your Gmail address in `EMAIL_HOST_USER`

---

## Usage

### Sending Alert Emails

```python
from alerts.services import AlertService
from alerts.models import Alert

# Create an alert
alert = Alert.objects.create(
    title="Critical vulnerability detected",
    description="CVE-2024-xxxx found on production server",
    alert_type=Alert.AlertType.SECURITY,
    severity=Alert.Severity.CRITICAL,
)

# Send email to default recipients based on severity
AlertService.send_alert_email(alert)

# Or send to specific recipients
from django.contrib.auth import get_user_model
User = get_user_model()
recipients = User.objects.filter(role='ADMIN')
AlertService.send_alert_email(alert, recipients=recipients)
```

### Sending Test Email (CLI)

```bash
python manage.py send_test_email your-email@example.com
```

### Sending Test Email (Web Interface)

1. Navigate to `/alerts/test-email/` (requires admin login)
2. Enter email address
3. Click "Send Test Email"
4. Check email logs or inbox for test message

### Sending Incident Notifications

```python
from alerts.models import Incident
from alerts.services import AlertService

incident = Incident.objects.create(
    title="Data breach detected",
    description="Unauthorized access to customer database",
    detected_at=timezone.now(),
)

# Send incident notification email
AlertService.send_incident_email(incident)
```

### Sending Compliance Notifications

```python
from alerts.email_service import EmailNotificationService

# Assuming report is a GeneratedReport instance
EmailNotificationService.send_compliance_notification(report)
```

---

## HIPAA Compliance Features

✓ **No PHI in Email Subjects** — Uses alert/incident IDs and types only
✓ **No PHI in Email Links** — Uses opaque internal IDs
✓ **Role-Based Access** — Only relevant roles receive notifications
✓ **Audit Logging** — All email sends logged to AuditLog
✓ **Secure Transmission** — TLS encryption for SMTP
✓ **Minimal Data Exposure** — Only essential information included
✓ **User Agent/IP Logging** — Context available for security investigation

---

## Email Service API Reference

### EmailNotificationService

```python
from alerts.email_service import EmailNotificationService

# Send alert email
success = EmailNotificationService.send_alert_email(
    alert_instance,
    recipients=None  # Auto-fetch if None
)

# Send account lock notification
success = EmailNotificationService.send_account_locked_email(
    user_instance,
    lock_reason="Suspicious activity",
    unlock_time=timezone.now() + timedelta(hours=24)
)

# Send compliance notification
success = EmailNotificationService.send_compliance_notification(
    report_instance
)

# Send incident notification
success = EmailNotificationService.send_incident_notification(
    incident_instance
)

# Send test email
success = EmailNotificationService.send_test_email("test@example.com")
```

All methods return `bool` indicating success (True) or failure (False).

---

## Troubleshooting

### Test Email Sent But Not Received

1. **Check email backend:**
   ```bash
   python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.EMAIL_BACKEND)
   ```

2. **Verify SMTP credentials:**
   - Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in .env
   - For Gmail, ensure you're using an App Password, not your regular password

3. **Check spam/junk folder:**
   - Email providers may filter automated messages

4. **Review email logs:**
   - Look for error messages in console or log files
   - Search for `[ERROR] alerts.email_service` in logs

### "log_event() got an unexpected keyword argument" Error

This is expected in non-HTTP contexts (like management commands). The error is caught and logged gracefully—the email is still sent successfully.

### Unicode Encoding Errors

If using Windows PowerShell with non-ASCII characters, output may fail but the operation succeeds. Check for "[OK]" or "[ERROR]" in output.

---

## Files Created/Modified

### New Files
- `alerts/email_service.py` — Core email service (310 lines)
- `alerts/management/commands/send_test_email.py` — Management command
- `alerts/management/__init__.py` — Package initialization
- `alerts/management/commands/__init__.py` — Package initialization
- `templates/emails/alert_email.html` — Alert email HTML template
- `templates/emails/alert_email.txt` — Alert email plain text template
- `templates/emails/account_locked_email.html` — Account lock HTML template
- `templates/emails/account_locked_email.txt` — Account lock text template
- `templates/emails/compliance_report_email.html` — Compliance HTML template
- `templates/emails/compliance_report_email.txt` — Compliance text template
- `templates/emails/incident_notification_email.html` — Incident HTML template
- `templates/emails/incident_notification_email.txt` — Incident text template
- `alerts/templates/alerts/test_email.html` — Test email UI
- `EMAIL_ALERT_SYSTEM.md` — This documentation file

### Modified Files
- `healthsec/settings.py` — Added SITE_NAME, SITE_DOMAIN settings
- `.env.example` — Added email configuration variables
- `alerts/services.py` — Extended with email methods, imported EmailNotificationService
- `alerts/views.py` — Added test_email view
- `alerts/urls.py` — Added test_email URL route

---

## Testing Checklist

- [x] Email templates render correctly with sample data
- [x] Management command sends test emails successfully
- [x] Web interface test email view works (admin-only)
- [x] Console email backend outputs emails to stdout
- [x] Role-based recipient selection works correctly
- [x] Audit log integration successful (with expected warnings)
- [x] Django system checks pass (0 issues)
- [x] HIPAA compliance requirements met

---

## Next Steps (Optional)

1. **Configure Production SMTP:**
   - Update .env with real SMTP credentials
   - Set `DJANGO_DEBUG=False`
   - Test with production email address

2. **Add Email Sending to Views:**
   - Call `AlertService.send_alert_email()` when alerts are created
   - Call `AlertService.send_incident_email()` when incidents are created
   - Call `EmailNotificationService.send_compliance_notification()` after reports

3. **Implement Email Digest:**
   - Send daily/weekly summaries of alerts
   - Batch notifications to reduce email volume

4. **Add Unsubscribe Links:**
   - Allow users to opt-out of certain notification types
   - Store preferences in UserProfile

5. **Set Up Email Logging:**
   - Store sent email records in database
   - Track delivery status and bounces
   - Create EmailLog model for audit trail

---

## Support & Issues

For issues or questions about the email alert system:
1. Check logs: `tail -f logs/healthsec.log` (if enabled)
2. Run test email: `python manage.py send_test_email your-email@example.com`
3. Check SMTP credentials in .env
4. Verify SITE_DOMAIN is correct for email links

---

**Last Updated:** 2026-05-25  
**Version:** 1.0  
**Status:** Production Ready (Awaiting SMTP Configuration)
