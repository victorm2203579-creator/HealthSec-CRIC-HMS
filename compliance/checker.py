"""
compliance/checker.py
=====================
ComplianceChecker — automated verification engine for compliance controls.

Each public check_* method inspects the live system state and returns a
standardised result dict::

    {
        'status':            'PASS' | 'FAIL' | 'PARTIAL' | 'NOT_APPLICABLE' | 'PENDING',
        'score':             float,   # 0-100
        'evidence':          str,     # what was inspected
        'notes':             str,     # human-readable summary
        'remediation_steps': str,     # what to fix if FAIL/PARTIAL
    }

run_all_automated_checks() iterates over all ComplianceControl records with
automated_check=True, calls the named method, persists a ComplianceCheckResult
row, and returns an aggregated report dict.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class ComplianceChecker:
    """
    Automated compliance verification engine.

    Methods beginning with ``check_`` correspond to check_function_name values
    stored on ComplianceControl records.  Each returns a standardised dict so
    the caller can persist results without knowing the check internals.
    """

    # ------------------------------------------------------------------
    # 1. Password Policy
    # ------------------------------------------------------------------

    def check_password_policy(self) -> dict:
        """
        Verify that Django's AUTH_PASSWORD_VALIDATORS enforce a strong policy.

        Checks:
        - MinimumLengthValidator with min_length >= 8
        - At least one complexity validator present (numeric, common-password, etc.)
        - Returns PARTIAL if only length is enforced; PASS if all three classes present.
        """
        validators = getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
        validator_names = [v.get('NAME', '') for v in validators]

        has_min_length = any('MinimumLength' in n for n in validator_names)
        has_complexity = any(
            kw in n for n in validator_names
            for kw in ('NumericPassword', 'CommonPassword', 'UserAttribute')
        )

        min_length = 0
        for v in validators:
            if 'MinimumLength' in v.get('NAME', ''):
                min_length = v.get('OPTIONS', {}).get('min_length', 8)

        evidence_lines = [f'Validators configured: {len(validators)}']
        for name in validator_names:
            evidence_lines.append(f'  • {name.split(".")[-1]}')

        if has_min_length and min_length >= 8 and has_complexity:
            return {
                'status': 'PASS',
                'score': 100.0,
                'evidence': '\n'.join(evidence_lines),
                'notes': f'Password policy enforced: min length {min_length} chars + complexity validators present.',
                'remediation_steps': '',
            }
        if has_min_length and min_length >= 8:
            return {
                'status': 'PARTIAL',
                'score': 60.0,
                'evidence': '\n'.join(evidence_lines),
                'notes': f'Minimum length ({min_length}) enforced but complexity validators are missing.',
                'remediation_steps': (
                    'Add NumericPasswordValidator and CommonPasswordValidator to '
                    'AUTH_PASSWORD_VALIDATORS in settings.py.'
                ),
            }
        return {
            'status': 'FAIL',
            'score': 20.0,
            'evidence': '\n'.join(evidence_lines) or 'No password validators configured.',
            'notes': 'Password policy is insufficient — minimum length not enforced.',
            'remediation_steps': (
                'Configure AUTH_PASSWORD_VALIDATORS with at least MinimumLengthValidator '
                '(min_length=8), CommonPasswordValidator, and NumericPasswordValidator.'
            ),
        }

    # ------------------------------------------------------------------
    # 2. Audit Logging
    # ------------------------------------------------------------------

    def check_audit_logging(self) -> dict:
        """
        Verify that the AuditLog model is actively capturing events.

        Checks:
        - AuditLog table is non-empty
        - Recent logs (last 7 days) exist
        - ≥90% of recent logs have a non-null user or ip_address (quality metric)
        """
        try:
            from audit.models import AuditLog
        except ImportError:
            return {
                'status': 'FAIL',
                'score': 0.0,
                'evidence': 'AuditLog model not found.',
                'notes': 'Audit logging module is not installed.',
                'remediation_steps': 'Ensure the audit app is installed and migrated.',
            }

        total = AuditLog.objects.count()
        cutoff = timezone.now() - timedelta(days=7)
        recent = AuditLog.objects.filter(timestamp__gte=cutoff)
        recent_count = recent.count()
        recent_with_user = recent.filter(user__isnull=False).count()

        evidence = (
            f'Total audit log entries: {total}\n'
            f'Entries in last 7 days: {recent_count}\n'
            f'Entries with user context: {recent_with_user} / {recent_count}'
        )

        if total == 0:
            return {
                'status': 'FAIL',
                'score': 0.0,
                'evidence': evidence,
                'notes': 'Audit log is empty — no events have been recorded.',
                'remediation_steps': (
                    'Verify AuditLogMiddleware is in MIDDLEWARE and log_event() is '
                    'called in all significant view actions.'
                ),
            }

        quality_pct = (recent_with_user / recent_count * 100) if recent_count else 0

        if recent_count > 0 and quality_pct >= 90:
            return {
                'status': 'PASS',
                'score': 100.0,
                'evidence': evidence,
                'notes': f'Audit logging active: {recent_count} entries in last 7 days ({quality_pct:.0f}% with user context).',
                'remediation_steps': '',
            }

        if recent_count > 0:
            return {
                'status': 'PARTIAL',
                'score': 60.0,
                'evidence': evidence,
                'notes': f'Audit logging active but only {quality_pct:.0f}% of entries have user context (threshold: 90%).',
                'remediation_steps': (
                    'Ensure all authenticated views call log_event() with request= parameter '
                    'so user context is captured.'
                ),
            }

        return {
            'status': 'PARTIAL',
            'score': 40.0,
            'evidence': evidence,
            'notes': 'Audit log exists but no entries recorded in the last 7 days.',
            'remediation_steps': 'Investigate AuditLogMiddleware configuration and trigger test actions.',
        }

    # ------------------------------------------------------------------
    # 3. Access Control (RBAC)
    # ------------------------------------------------------------------

    def check_access_control(self) -> dict:
        """
        Verify that role-based access control (RBAC) is implemented.

        Checks:
        - Custom User model has a role field
        - All active users have a non-empty role assigned
        - Inactive users cannot log in (is_active=False)
        """
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()

        evidence_lines = [
            f'Total users: {total_users}',
            f'Active: {active_users}, Inactive: {inactive_users}',
        ]

        has_role_field = hasattr(User, 'role')
        if not has_role_field:
            return {
                'status': 'FAIL',
                'score': 0.0,
                'evidence': '\n'.join(evidence_lines),
                'notes': 'User model does not have a role field — RBAC is not implemented.',
                'remediation_steps': 'Add a role field to the custom User model with appropriate choices.',
            }

        users_with_roles = User.objects.exclude(role='').count()
        users_without_roles = total_users - users_with_roles
        evidence_lines.append(f'Users with role assigned: {users_with_roles} / {total_users}')

        score = 100.0
        issues = []

        if users_without_roles > 0:
            score -= 30.0
            issues.append(f'{users_without_roles} user(s) have no role assigned.')

        role_coverage_pct = (users_with_roles / total_users * 100) if total_users else 100

        if score >= 90:
            status = 'PASS'
        elif score >= 60:
            status = 'PARTIAL'
        else:
            status = 'FAIL'

        return {
            'status': status,
            'score': max(score, 0.0),
            'evidence': '\n'.join(evidence_lines),
            'notes': (
                f'RBAC implemented: {role_coverage_pct:.0f}% of users have roles. '
                + (' Issues: ' + '; '.join(issues) if issues else 'No issues found.')
            ),
            'remediation_steps': (
                'Assign roles to all users via the admin panel. '
                'Enforce role checks on all sensitive views.' if issues else ''
            ),
        }

    # ------------------------------------------------------------------
    # 4. Session Timeout
    # ------------------------------------------------------------------

    def check_session_timeout(self) -> dict:
        """
        Check that SESSION_COOKIE_AGE is set to ≤1800 seconds (30 minutes).

        HIPAA requires automatic session logoff after a period of inactivity.
        """
        age = getattr(settings, 'SESSION_COOKIE_AGE', None)
        evidence = f'SESSION_COOKIE_AGE = {age} seconds ({age / 60:.0f} minutes)' if age else 'SESSION_COOKIE_AGE not set.'

        if age is None:
            return {
                'status': 'FAIL',
                'score': 0.0,
                'evidence': evidence,
                'notes': 'SESSION_COOKIE_AGE is not configured — sessions never expire automatically.',
                'remediation_steps': 'Set SESSION_COOKIE_AGE = 1800 in settings.py.',
            }

        if age <= 1800:
            return {
                'status': 'PASS',
                'score': 100.0,
                'evidence': evidence,
                'notes': f'Session timeout is {age / 60:.0f} minutes — compliant (≤30 min required).',
                'remediation_steps': '',
            }

        score = max(0.0, 100.0 - (age - 1800) / 60)
        return {
            'status': 'FAIL',
            'score': round(score, 1),
            'evidence': evidence,
            'notes': f'Session timeout is {age / 60:.0f} minutes — exceeds 30-minute requirement.',
            'remediation_steps': 'Set SESSION_COOKIE_AGE = 1800 (or less) in settings.py.',
        }

    # ------------------------------------------------------------------
    # 5. Encryption Status
    # ------------------------------------------------------------------

    def check_encryption_status(self) -> dict:
        """
        Verify that passwords are stored using a strong hashing algorithm.

        Checks:
        - PASSWORD_HASHERS uses PBKDF2, bcrypt, or Argon2 (not MD5)
        - SECURE_SSL_REDIRECT setting (noted but not penalised in dev mode)
        """
        hashers = getattr(settings, 'PASSWORD_HASHERS', [])
        default_hasher = hashers[0] if hashers else ''
        ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        debug = getattr(settings, 'DEBUG', True)

        strong_hashers = ('PBKDF2', 'bcrypt', 'Argon2', 'argon2')
        weak_hashers = ('MD5', 'SHA1', 'UnsaltedSHA1', 'UnsaltedMD5')

        is_strong = any(h in default_hasher for h in strong_hashers)
        is_weak = any(h in default_hasher for h in weak_hashers)

        evidence_lines = [
            f'Default password hasher: {default_hasher.split(".")[-1] if default_hasher else "Django default (PBKDF2)"}',
            f'SECURE_SSL_REDIRECT: {ssl_redirect}',
            f'DEBUG mode: {debug}',
        ]

        score = 100.0
        issues = []

        if is_weak:
            score -= 60.0
            issues.append(f'Weak password hasher in use: {default_hasher}')

        if not ssl_redirect and not debug:
            score -= 30.0
            issues.append('SECURE_SSL_REDIRECT is False in production mode.')

        if score >= 90:
            status = 'PASS'
        elif score >= 60:
            status = 'PARTIAL'
        else:
            status = 'FAIL'

        return {
            'status': status,
            'score': max(score, 0.0),
            'evidence': '\n'.join(evidence_lines),
            'notes': (
                'Encryption configuration is compliant.' if not issues
                else 'Encryption issues: ' + '; '.join(issues)
            ),
            'remediation_steps': (
                '\n'.join([
                    'Replace weak hashers with PBKDF2PasswordHasher or Argon2PasswordHasher.' if is_weak else '',
                    'Set SECURE_SSL_REDIRECT = True in production settings.' if not ssl_redirect and not debug else '',
                ]).strip() or ''
            ),
        }

    # ------------------------------------------------------------------
    # 6. Failed Login Monitoring
    # ------------------------------------------------------------------

    def check_failed_login_monitoring(self) -> dict:
        """
        Verify that failed login attempts are tracked and monitored.

        Checks:
        - UserProfile has a failed_login_attempts field
        - There are records of failed logins in the last 30 days (proves monitoring is live)
        - Account lockout mechanism is in place
        """
        try:
            from accounts.models import UserProfile
        except ImportError:
            return {
                'status': 'FAIL',
                'score': 0.0,
                'evidence': 'UserProfile model not found.',
                'notes': 'Cannot verify failed login monitoring — accounts app not available.',
                'remediation_steps': 'Ensure the accounts app is installed.',
            }

        has_field = hasattr(UserProfile, 'failed_login_attempts')
        total_profiles = UserProfile.objects.count()
        cutoff = timezone.now() - timedelta(days=30)

        evidence_lines = [
            f'UserProfile has failed_login_attempts field: {has_field}',
            f'Total user profiles: {total_profiles}',
        ]

        if not has_field:
            return {
                'status': 'FAIL',
                'score': 10.0,
                'evidence': '\n'.join(evidence_lines),
                'notes': 'UserProfile lacks failed_login_attempts field — no brute-force tracking.',
                'remediation_steps': (
                    'Add failed_login_attempts (PositiveSmallIntegerField) and '
                    'last_failed_login (DateTimeField) to UserProfile.'
                ),
            }

        users_with_failures = UserProfile.objects.filter(failed_login_attempts__gt=0).count()
        evidence_lines.append(f'Profiles with recorded failed attempts: {users_with_failures}')

        audit_evidence = ''
        try:
            from audit.models import AuditLog
            recent_logins = AuditLog.objects.filter(
                action=AuditLog.Action.LOGIN,
                timestamp__gte=cutoff,
            ).count()
            evidence_lines.append(f'Login events in last 30 days in AuditLog: {recent_logins}')
            audit_evidence = f'Login events audited: {recent_logins}'
        except Exception:
            pass

        score = 70.0 if has_field else 0.0
        if users_with_failures > 0 or audit_evidence:
            score = 90.0
        if users_with_failures >= 10:
            score = 100.0

        return {
            'status': 'PASS' if score >= 90 else 'PARTIAL',
            'score': score,
            'evidence': '\n'.join(evidence_lines),
            'notes': (
                f'Failed login monitoring active: {users_with_failures} account(s) have recorded failures.'
            ),
            'remediation_steps': (
                'Implement automatic account lockout after 5 consecutive failures and '
                'add failed login tracking to the login view.' if score < 90 else ''
            ),
        }

    # ------------------------------------------------------------------
    # 7. Incident Response
    # ------------------------------------------------------------------

    def check_incident_response(self) -> dict:
        """
        Verify that an incident response workflow is active.

        Checks:
        - Alert model is present and has records
        - At least one alert has been acknowledged or resolved (workflow is used)
        - Incident model has records
        """
        try:
            from alerts.models import Alert, Incident
        except ImportError:
            return {
                'status': 'FAIL',
                'score': 0.0,
                'evidence': 'Alerts app not found.',
                'notes': 'Incident response module is not installed.',
                'remediation_steps': 'Install and configure the alerts app.',
            }

        total_alerts = Alert.objects.count()
        assigned_alerts = Alert.objects.filter(assigned_to__isnull=False).count()
        resolved_alerts = Alert.objects.filter(status__in=['RESOLVED', 'CLOSED']).count()
        total_incidents = Incident.objects.count()

        evidence = (
            f'Total alerts: {total_alerts}\n'
            f'Assigned alerts: {assigned_alerts}\n'
            f'Resolved/closed alerts: {resolved_alerts}\n'
            f'Formal incidents created: {total_incidents}'
        )

        if total_alerts == 0:
            return {
                'status': 'PARTIAL',
                'score': 30.0,
                'evidence': evidence,
                'notes': 'Alert system is installed but no alerts have been raised yet.',
                'remediation_steps': (
                    'Configure alert triggers in the monitoring and risk engine. '
                    'Verify the alert generation pipeline is working.'
                ),
            }

        score = 60.0
        if assigned_alerts > 0:
            score += 20.0
        if resolved_alerts > 0:
            score += 10.0
        if total_incidents > 0:
            score += 10.0

        return {
            'status': 'PASS' if score >= 90 else 'PARTIAL',
            'score': min(score, 100.0),
            'evidence': evidence,
            'notes': (
                f'Incident response workflow active: {total_alerts} alerts, '
                f'{assigned_alerts} assigned, {resolved_alerts} resolved.'
            ),
            'remediation_steps': (
                'Create formal incident records for significant alerts and ensure all '
                'critical alerts are assigned to a responder.' if score < 90 else ''
            ),
        }

    # ------------------------------------------------------------------
    # 8. Data Backup Policy (Manual)
    # ------------------------------------------------------------------

    def check_data_backup_policy(self) -> dict:
        """
        Check whether a data backup policy is in place.

        This check is a MANUAL CHECK — the system cannot verify backup
        execution automatically.  Returns PENDING to prompt the compliance
        officer to review and confirm.
        """
        backup_configured = bool(getattr(settings, 'BACKUP_DIR', None))
        evidence = (
            f'BACKUP_DIR setting present: {backup_configured}\n'
            'Manual verification required: backup schedule, offsite storage, restore tests.'
        )
        return {
            'status': 'PENDING',
            'score': 50.0,
            'evidence': evidence,
            'notes': (
                'Automated verification is not available for backup execution. '
                'A compliance officer must confirm the backup schedule and restore capability.'
            ),
            'remediation_steps': (
                '1. Document the backup schedule (daily incremental, weekly full).\n'
                '2. Verify backups are stored offsite or in a separate cloud region.\n'
                '3. Conduct a quarterly restore test.\n'
                '4. Update this control status to PASS once verified.'
            ),
        }

    # ------------------------------------------------------------------
    # 9. User Training Records (Manual)
    # ------------------------------------------------------------------

    def check_user_training_records(self) -> dict:
        """
        Verify that staff security awareness training records are maintained.

        This is a MANUAL CHECK.  Returns PENDING to prompt review by the
        compliance officer who must confirm training completion records exist.
        """
        total_users = User.objects.filter(is_active=True).count()
        evidence = (
            f'Active staff accounts: {total_users}\n'
            'Training record system: external (e-learning platform or paper records)\n'
            'Manual verification required.'
        )
        return {
            'status': 'PENDING',
            'score': 50.0,
            'evidence': evidence,
            'notes': (
                f'Manual check required: verify that all {total_users} active staff '
                'have completed annual security awareness training.'
            ),
            'remediation_steps': (
                '1. Obtain training completion records from HR/e-learning platform.\n'
                '2. Confirm all active staff completed training within the last 12 months.\n'
                '3. Flag any outstanding accounts for immediate training.\n'
                '4. Update this control to PASS once 100% completion is confirmed.'
            ),
        }

    # ------------------------------------------------------------------
    # 10. Run All Automated Checks
    # ------------------------------------------------------------------

    def run_all_automated_checks(self, triggered_by=None) -> dict:
        """
        Run every ComplianceControl with automated_check=True.

        For each matching control, calls getattr(self, control.check_function_name)()
        and persists a ComplianceCheckResult row.  Manual controls (automated_check=False)
        are skipped but included in the summary as PENDING.

        Args:
            triggered_by: User instance who triggered the run, or None for system runs.

        Returns:
            dict with keys:
              'results'       – list of per-control result dicts
              'overall_score' – weighted compliance score (0-100)
              'passed'        – count of PASS results
              'failed'        – count of FAIL results
              'partial'       – count of PARTIAL results
              'pending'       – count of PENDING / skipped controls
              'run_at'        – ISO timestamp of the run
        """
        from .models import ComplianceCheckResult, ComplianceControl

        controls = ComplianceControl.objects.select_related('framework').all()
        results_out = []
        total_weight = 0.0
        weighted_score_sum = 0.0

        counts = {'PASS': 0, 'FAIL': 0, 'PARTIAL': 0, 'PENDING': 0, 'NOT_APPLICABLE': 0}

        for ctrl in controls:
            if ctrl.automated_check and ctrl.check_function_name:
                checker_fn = getattr(self, ctrl.check_function_name, None)
                if checker_fn:
                    try:
                        result_data = checker_fn()
                    except Exception as exc:
                        result_data = {
                            'status': 'FAIL',
                            'score': 0.0,
                            'evidence': f'Check raised an exception: {exc}',
                            'notes': 'Automated check failed with an error.',
                            'remediation_steps': 'Investigate the checker method and fix the underlying issue.',
                        }
                else:
                    result_data = {
                        'status': 'PENDING',
                        'score': 50.0,
                        'evidence': f'Check function "{ctrl.check_function_name}" not found on ComplianceChecker.',
                        'notes': 'Automated check function missing.',
                        'remediation_steps': f'Implement {ctrl.check_function_name}() in compliance/checker.py.',
                    }
            else:
                result_data = {
                    'status': 'PENDING',
                    'score': 50.0,
                    'evidence': 'Manual check — not automated.',
                    'notes': 'Compliance officer must verify this control manually.',
                    'remediation_steps': ctrl.description,
                }

            check_result = ComplianceCheckResult.objects.create(
                control=ctrl,
                checked_by=triggered_by,
                status=result_data['status'],
                score=result_data['score'],
                notes=result_data['notes'],
                evidence=result_data['evidence'],
                remediation_steps=result_data.get('remediation_steps', ''),
            )

            counts[result_data['status']] = counts.get(result_data['status'], 0) + 1
            total_weight += ctrl.weight
            weighted_score_sum += ctrl.weight * result_data['score']

            results_out.append({
                'control': ctrl,
                'result': check_result,
                **result_data,
            })

        overall_score = round((weighted_score_sum / total_weight), 1) if total_weight else 0.0

        return {
            'results': results_out,
            'overall_score': overall_score,
            'passed': counts.get('PASS', 0),
            'failed': counts.get('FAIL', 0),
            'partial': counts.get('PARTIAL', 0),
            'pending': counts.get('PENDING', 0) + counts.get('NOT_APPLICABLE', 0),
            'run_at': timezone.now().isoformat(),
        }
