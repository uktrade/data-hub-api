from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

from core.mixins import DeferredSaveModelMixin


class BaseModel(DeferredSaveModelMixin, models.Model):
    """Common fields for most of the models we use."""

    archived = models.BooleanField(default=False)
    archived_on = models.DateTimeField(default=now, null=True)
    archived_reason = models.TextField(null=True)
    archived_by = models.ForeignKey(User, null=True)

    class Meta:
        abstract = True

    def archive(self, reason=None):
        """Archive the model instance."""
        self.archived = True
        self.archived_reason = reason
        self.save()


class BaseConstantModel(models.Model):
    """Constant tables for FKs."""

    id = models.UUIDField(primary_key=True)
    name = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ('name', )

    def __str__(self):
        return self.name
