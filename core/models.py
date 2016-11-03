from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

from core.mixins import DeferredSaveModelMixin


class BaseModel(DeferredSaveModelMixin, models.Model):
    """Common fields for most of the models we use."""

    archived = models.BooleanField(default=False)
    archived_on = models.DateTimeField(null=True)
    archived_reason = models.TextField(blank=True, null=True)
    archived_by = models.ForeignKey(User, null=True)
    created_on = models.DateTimeField(null=True, blank=True)
    modified_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def archive(self, reason=None):
        """Archive the model instance."""

        self.archived = True
        self.archived_reason = reason
        self.save()

    def unarchive(self):
        """Unarchive the model instance."""

        self.archived = False
        self.archived_reason = ''
        self.save()

    def clean(self):
        """Custom validation for created_on and modified_on.

        If the fields are empty, populate them.
        """

        self.created_on = self.created_on if self.created_on else now()
        self.modified_on = self.modified_on if self.modified_on else now()


class BaseConstantModel(models.Model):
    """Constant tables for FKs."""

    id = models.UUIDField(primary_key=True)
    name = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ('name', )

    def __str__(self):
        return self.name
