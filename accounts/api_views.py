"""
accounts/api_views.py
=====================
DRF ViewSets for the accounts API.
"""

from rest_framework import serializers, viewsets, permissions
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'role', 'department', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and retrieving users (read-only)."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Non-admin users only see their own record
        user = self.request.user
        if user.is_admin:
            return User.objects.all().order_by('username')
        return User.objects.filter(pk=user.pk)
