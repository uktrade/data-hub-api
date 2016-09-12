"""Mixins."""

from django.core.exceptions import PermissionDenied


class ReadOnlyModelMixin:
    """Prevents models from adding, deleting and updating."""

    def save(self, *args, **kwargs):
        """Save is not allowed."""
        raise PermissionDenied('This model is read-only')

    def delete(self, *args, **kwargs):
        """Delete is not allowed."""
        raise PermissionDenied('This model is read-only')
