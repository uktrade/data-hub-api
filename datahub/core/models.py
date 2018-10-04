from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from datahub.core.utils import join_truthy_strings


class BaseModel(models.Model):
    """Common fields for most of the models we use."""

    created_on = models.DateTimeField(db_index=True, null=True, blank=True, auto_now_add=True)
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    class Meta:
        abstract = True


class ArchivableModel(models.Model):
    """Handle model archivation."""

    archived = models.BooleanField(default=False)
    archived_on = models.DateTimeField(blank=True, null=True)
    archived_reason = models.TextField(blank=True, null=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='+',
    )

    class Meta:
        abstract = True

    def archive(self, user, reason=None):
        """Archive the model instance."""
        self.archived = True
        self.archived_by = user
        self.archived_reason = reason
        self.archived_on = now()
        self.save()

    def unarchive(self):
        """Unarchive the model instance."""
        self.archived = False
        self.archived_reason = ''
        self.archived_by = None
        self.archived_on = None
        self.save()


class DisableableModel(models.Model):
    """Defines a disabled_on field and related logic."""

    disabled_on = models.DateTimeField(blank=True, null=True)

    def was_disabled_on(self, date_on):
        """Returns True if this object was disabled at time `date_on`, False otherwise."""
        if not self.disabled_on:
            return False
        return self.disabled_on <= date_on

    class Meta:
        abstract = True


class BaseConstantModel(DisableableModel):
    """Constant tables for FKs."""

    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ('name', )

    def __str__(self):
        """Human readable admin name."""
        return join_truthy_strings(
            self.name,
            '(disabled)' if self.disabled_on else None,
        )


class BaseOrderedConstantModel(BaseConstantModel):
    """Constants where values are manually ordered (by the order column) when displayed."""

    # Uses a float to make reordering easier
    order = models.FloatField(default=0.0)

    class Meta:
        abstract = True
        ordering = ('order', )
