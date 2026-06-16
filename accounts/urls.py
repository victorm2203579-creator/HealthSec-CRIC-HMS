"""
accounts/urls.py
================
URL patterns for the accounts app (HTML views).
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password/change/', views.change_password_view, name='change_password'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/new/', views.register_user_view, name='register'),
    # 2FA routes
    path('2fa/verify/', views.totp_verify_view, name='totp_verify'),
    path('2fa/setup/', views.totp_setup_view, name='totp_setup'),
    path('2fa/backup-codes/', views.totp_backup_codes_view, name='totp_backup_codes'),
    path('2fa/disable/', views.totp_disable_view, name='totp_disable'),
]
