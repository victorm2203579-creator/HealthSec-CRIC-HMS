"""
accounts/signals.py
===================
Django signals for the accounts app.

Automatically creates a UserProfile whenever a new User is saved so
every user always has an associated profile record.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a blank UserProfile the first time a User is saved."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Keep the UserProfile in sync whenever the User is updated."""
    # Guard: profile may not exist yet on the very first save (race condition)
    if hasattr(instance, 'profile'):
        instance.profile.save()
