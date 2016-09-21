"""General mixins."""

from dummy_writing_layer.services import delete_model, save_model


class DeferredWritingOperationsModelMixin:
    """Handles adding, deleting and updating.

    Writing operations (add, delete, update) should be
    deferred to the Korben client library.

    Some temporary glue code is in place, allowing Django to handle the writing operations
    and the ElasticSearch update.
    This will be removed as soon as the Korben client is ready.
    """

    def save(self, *args, **kwargs):
        """Save is temporarily allowed, also write to ES."""
        super().save(*args, **kwargs)
        save_model(self)

    def delete(self, *args, **kwargs):
        """Delete is temporarily allowed, also write to ES."""
        super().save(*args, **kwargs)
        delete_model(self)
