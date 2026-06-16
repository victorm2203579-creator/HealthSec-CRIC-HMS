"""
accounts/admin.py
=================
Django admin registrations for the accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline profile editing on the User admin page."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin view for the extended User model."""

    inlines = (UserProfileInline,)

    # Columns shown in the user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')

    search_fields = ('username', 'email', 'first_name', 'last_name', 'department')
    ordering = ('username',)

    def get_fieldsets(self, request, obj=None):
        """Dynamically add HealthSec fields to fieldsets."""
        fieldsets = super().get_fieldsets(request, obj)
        healthsec_fieldset = ('HealthSec Role & Contact', {
            'fields': ('role', 'department', 'phone_number', 'avatar', 'must_change_password'),
        })
        return list(fieldsets) + [healthsec_fieldset]

    def get_add_fieldsets(self, request):
        """Dynamically add HealthSec fields to add_fieldsets."""
        fieldsets = super().get_add_fieldsets(request)
        healthsec_fieldset = ('HealthSec Role & Contact', {
            'fields': ('role', 'department', 'email'),
        })
        return list(fieldsets) + [healthsec_fieldset]
