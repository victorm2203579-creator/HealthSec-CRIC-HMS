# healthsec package initializer
# This file marks the healthsec directory as a Python package (the Django project config package)

# --- Python 3.14 / Django 4.2 compatibility patch ----
# Bug: Django 4.2 (and 5.0, 5.1) has BaseContext.__copy__() call copy(super())
# instead of copy(self), which breaks on Python 3.14+ because super() proxies
# no longer expose __dict__ for the copy module to introspect.
# Error: AttributeError: 'super' object has no attribute 'dicts'
# This happens whenever a template Context is copied (admin forms, error pages).
#
# Fix: Self-healing monkeypatch. Verifies the installed Django is actually
# broken before patching (so upgrades to Django versions with the real fix
# become automatic no-ops instead of double-patching).
#
# Timeline: Django 4.2+ until fixed upstream (as of June 2026, not yet).
# Python: 3.14+.
#
import copy as _copy_module
from django.template.context import BaseContext as _BaseContext

_PATCH_APPLIED = False

try:
    _copy_module.copy(_BaseContext())
    # If copy succeeds, Django already has the fix or this is Python 3.13.
    _PATCH_NEEDED = False
except AttributeError as e:
    # AttributeError on copy = broken Django + Python 3.14+
    if 'dicts' in str(e) or '__dict__' in str(e):
        _PATCH_NEEDED = True
    else:
        raise

if _PATCH_NEEDED:
    def _patched_context_copy(self):
        """Manual shallow copy avoiding the super() proxy bug."""
        duplicate = object.__new__(type(self))
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    _BaseContext.__copy__ = _patched_context_copy
    _PATCH_APPLIED = True

# Cleanup
del _copy_module, _BaseContext, _PATCH_NEEDED
if '_patched_context_copy' in locals():
    del _patched_context_copy
# -------------------------------------------------------
