"""
accounts/views.py
=================
View functions / class-based views for user authentication and profile management.

Covers:
  - Login / logout (with audit logging of login events)
  - User registration (admin-initiated only; no public sign-up)
  - Password change (enforced on first login)
  - User profile view / edit
  - User management list (ADMIN role only)
"""

import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from audit.utils import log_event
from .forms import LoginForm, UserRegistrationForm, UserProfileForm
from .models import User, UserProfile, LoginHistory, TwoFactorAuth

try:
    from .geoip_service import GeoIPService
except ImportError:
    GeoIPService = None

try:
    from .totp_service import TOTPService
except ImportError:
    TOTPService = None

try:
    from user_agents import parse as parse_user_agent
except ImportError:
    parse_user_agent = None

logger = logging.getLogger('healthsec.accounts')

try:
    from django_ratelimit.decorators import ratelimit as _ratelimit
    _RATELIMIT_AVAILABLE = True
except ImportError:
    _ratelimit = None
    _RATELIMIT_AVAILABLE = False


def _rate_limited(request):
    """Return True when the request was blocked by the rate limiter."""
    return getattr(request, 'limited', False)


def login_view(request):
    """Authenticate the user — rate limited to 10 attempts / minute per IP."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    # Apply rate limit when django-ratelimit is installed
    if _RATELIMIT_AVAILABLE and request.method == 'POST':
        decorated = _ratelimit(key='ip', rate='10/m', method='POST', block=True)(lambda r: None)
        try:
            decorated(request)
        except Exception:
            pass
        if _rate_limited(request):
            messages.error(request, "Too many login attempts. Please wait a minute and try again.")
            return render(request, 'accounts/login.html', {'form': LoginForm()})

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            client_ip = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            device_info = ''

            # Capture device info if user_agents available
            if parse_user_agent:
                try:
                    ua = parse_user_agent(user_agent)
                    device_info = f"{ua.os.family} {ua.os.version_string} - {ua.browser.family}"
                except Exception:
                    pass

            # Capture IP and location data if GeoIPService available
            location = {'city': '', 'country': '', 'country_code': '', 'latitude': None, 'longitude': None}
            is_suspicious = False
            suspicious_reason = ''

            if GeoIPService:
                try:
                    geoip_service = GeoIPService()
                    location = geoip_service.get_location(client_ip)
                    is_suspicious, suspicious_reason = geoip_service.is_suspicious_location(user, client_ip)
                except Exception as e:
                    logger.warning('GeoIP lookup failed: %s', str(e))

            # Create LoginHistory record if LoginHistory model exists
            login_history = None
            try:
                login_history = LoginHistory.objects.create(
                    user=user,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    device_info=device_info,
                    city=location.get('city', ''),
                    country=location.get('country', ''),
                    country_code=location.get('country_code', ''),
                    latitude=location.get('latitude'),
                    longitude=location.get('longitude'),
                    is_suspicious=is_suspicious,
                    suspicious_reason=suspicious_reason,
                    success=True,
                )
            except Exception as e:
                logger.warning('Failed to create LoginHistory: %s', str(e))

            # Check if 2FA is required if TOTPService available
            needs_2fa = False
            if TOTPService:
                try:
                    totp_service = TOTPService()
                    needs_2fa = totp_service.enforce_2fa_for_role(user) and user.totp_auth.is_enabled
                except Exception:
                    needs_2fa = False

            if needs_2fa and login_history:
                request.session['2fa_user_id'] = user.id
                request.session['2fa_login_id'] = login_history.id
                return redirect('accounts:totp_verify')

            # Complete login
            login(request, user)
            user.last_login_ip = client_ip
            user.save(update_fields=['last_login_ip'])

            log_event(
                user=user,
                action='LOGIN',
                description=f'User {username} logged in successfully.',
                request=request,
            )

            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
            logger.warning('Failed login attempt for username: %s', username)

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
@login_required
def logout_view(request):
    """Log the user out and redirect to the login page."""
    log_event(
        user=request.user,
        action='LOGOUT',
        description=f'User {request.user.username} logged out.',
        request=request,
    )
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Display and update the current user's profile."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = UserProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=profile,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@login_required
def change_password_view(request):
    """Allow users to change their own password."""
    form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        # Keep the session alive after password change
        update_session_auth_hash(request, user)
        # Clear the forced-change flag
        user.must_change_password = False
        user.save(update_fields=['must_change_password'])
        log_event(
            user=user,
            action='PASSWORD_CHANGE',
            description='User changed their password.',
            request=request,
        )
        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def user_list_view(request):
    """List all system users – accessible by ADMIN role only."""
    if not request.user.is_admin:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:index')

    users = User.objects.select_related('profile').order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def register_user_view(request):
    """Admin-only: create a new system user account."""
    if not request.user.is_admin:
        messages.error(request, 'Only administrators can create new accounts.')
        return redirect('dashboard:index')

    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_user = form.save()
        log_event(
            user=request.user,
            action='USER_CREATED',
            description=f'Admin created new user account: {new_user.username}',
            request=request,
        )
        messages.success(request, f'Account created for {new_user.username}.')
        return redirect('accounts:user_list')

    return render(request, 'accounts/register.html', {'form': form})


def totp_verify_view(request):
    """Verify TOTP code during login."""
    user_id = request.session.get('2fa_user_id')
    login_id = request.session.get('2fa_login_id')

    if not user_id:
        return redirect('accounts:login')

    try:
        user = User.objects.get(id=user_id)
        login_history = LoginHistory.objects.get(id=login_id)
    except (User.DoesNotExist, LoginHistory.DoesNotExist):
        return redirect('accounts:login')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        use_backup = request.POST.get('use_backup', False)

        totp_service = TOTPService()

        if use_backup:
            # Verify backup code
            try:
                totp_auth = user.totp_auth
                if totp_service.use_backup_code(totp_auth.backup_codes, code):
                    totp_auth.backup_codes = [c for c in totp_auth.backup_codes if c != code]
                    totp_auth.last_used = timezone.now()
                    totp_auth.save()

                    # Complete login
                    login(request, user)
                    user.last_login_ip = login_history.ip_address
                    user.save(update_fields=['last_login_ip'])

                    log_event(
                        user=user,
                        action='LOGIN',
                        description=f'User {user.username} logged in successfully (2FA with backup code).',
                        request=request,
                    )

                    # Clear 2FA session data
                    del request.session['2fa_user_id']
                    del request.session['2fa_login_id']

                    next_url = request.GET.get('next', 'dashboard:index')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Invalid backup code.')
            except TwoFactorAuth.DoesNotExist:
                messages.error(request, '2FA not configured.')
        else:
            # Verify TOTP code
            try:
                totp_auth = user.totp_auth
                if totp_service.verify_code(totp_auth.secret_key, code):
                    totp_auth.last_used = timezone.now()
                    totp_auth.save()

                    # Complete login
                    login(request, user)
                    user.last_login_ip = login_history.ip_address
                    user.save(update_fields=['last_login_ip'])

                    log_event(
                        user=user,
                        action='LOGIN',
                        description=f'User {user.username} logged in successfully (2FA verified).',
                        request=request,
                    )

                    # Clear 2FA session data
                    del request.session['2fa_user_id']
                    del request.session['2fa_login_id']

                    next_url = request.GET.get('next', 'dashboard:index')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Invalid authentication code.')
            except TwoFactorAuth.DoesNotExist:
                messages.error(request, '2FA not configured.')

    return render(request, 'accounts/totp_verify.html', {'user': user})


@login_required
def totp_setup_view(request):
    """Setup TOTP 2FA for the current user."""
    totp_auth, created = TwoFactorAuth.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'generate':
            # Generate new secret
            totp_service = TOTPService()
            totp_auth.secret_key = totp_service.generate_secret()
            totp_auth.is_verified = False
            totp_auth.save()
            messages.info(request, 'New secret generated. Scan the QR code below.')
            return redirect('accounts:totp_setup')

        elif action == 'verify':
            # Verify TOTP code
            code = request.POST.get('code', '').strip()
            totp_service = TOTPService()

            if totp_service.verify_code(totp_auth.secret_key, code):
                # Generate backup codes
                backup_codes = totp_service.generate_backup_codes(10)
                totp_auth.backup_codes = backup_codes
                totp_auth.is_verified = True
                totp_auth.save()

                log_event(
                    user=request.user,
                    action='2FA_SETUP',
                    description='User configured TOTP 2FA.',
                    request=request,
                )

                messages.success(request, '2FA configured successfully. Save your backup codes!')
                return redirect('accounts:totp_backup_codes')
            else:
                messages.error(request, 'Invalid code. Please try again.')

        elif action == 'enable':
            # Enable 2FA if verified
            if totp_auth.is_verified:
                totp_auth.is_enabled = True
                totp_auth.enabled_at = timezone.now()
                totp_auth.save()

                log_event(
                    user=request.user,
                    action='2FA_ENABLED',
                    description='User enabled TOTP 2FA.',
                    request=request,
                )

                messages.success(request, '2FA is now enabled.')
                return redirect('accounts:profile')
            else:
                messages.error(request, 'Please verify your code first.')

    # Generate QR code if secret exists
    qr_code_data = None
    if totp_auth.secret_key and not totp_auth.is_verified:
        totp_service = TOTPService()
        qr_code_data = totp_service.generate_qr_code(
            totp_auth.secret_key,
            request.user.email,
            'HealthSec'
        )

    return render(request, 'accounts/totp_setup.html', {
        'totp_auth': totp_auth,
        'qr_code_data': qr_code_data,
    })


@login_required
def totp_backup_codes_view(request):
    """Display backup codes after 2FA setup."""
    try:
        totp_auth = request.user.totp_auth
    except TwoFactorAuth.DoesNotExist:
        return redirect('accounts:profile')

    if not totp_auth.backup_codes:
        return redirect('accounts:totp_setup')

    context = {
        'backup_codes': totp_auth.backup_codes,
    }
    return render(request, 'accounts/totp_backup_codes.html', context)


@login_required
def totp_disable_view(request):
    """Disable 2FA for the current user."""
    try:
        totp_auth = request.user.totp_auth
    except TwoFactorAuth.DoesNotExist:
        messages.info(request, '2FA is not configured.')
        return redirect('accounts:profile')

    if request.method == 'POST':
        totp_auth.is_enabled = False
        totp_auth.is_verified = False
        totp_auth.backup_codes = []
        totp_auth.save()

        log_event(
            user=request.user,
            action='2FA_DISABLED',
            description='User disabled TOTP 2FA.',
            request=request,
        )

        messages.success(request, '2FA has been disabled.')
        return redirect('accounts:profile')

    return render(request, 'accounts/totp_disable.html', {'totp_auth': totp_auth})


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _get_client_ip(request) -> str:
    """Extract the real client IP from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
