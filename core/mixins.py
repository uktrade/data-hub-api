"""General mixins."""

from es.services import save_model


class DeferredSaveModelMixin:
    """Handles add and update models."""

    def save(self, *args, **kwargs):
        """Save is temporarily allowed, also write to ES."""
        super().save(*args, **kwargs)
        save_model(self)
