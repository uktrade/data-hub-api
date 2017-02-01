from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now

from datahub.company import tasks


class BaseModel(models.Model):
    """Common fields for most of the models we use."""

    created_on = models.DateTimeField(null=True, blank=True)
    modified_on = models.DateTimeField(null=True, blank=True)

    class Meta:  # noqa: D101
        abstract = True

    def clean(self):
        """Custom validation for created_on and modified_on.

        If the fields are empty, populate them.
        """
        super().clean()
        current_time = now()
        self.created_on = self.created_on or current_time
        self.modified_on = current_time

    def get_datetime_fields(self):
        """Return list of fields that should be mapped as datetime."""
        fields = super().get_datetime_fields()
        return fields + ['created_on', 'modified_on']


class ArchivableModel(models.Model):
    """Handle model archivation."""

    archived = models.BooleanField(default=False)
    archived_on = models.DateTimeField(null=True)
    archived_reason = models.TextField(blank=True, null=True)
    archived_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    class Meta:  # noqa: D101
        abstract = True

    def archive(self, user, reason=None):
        """Archive the model instance."""
        self.archived = True
        self.archived_by = user
        self.archived_reason = reason
        self.archived_on = now()
        self.save(skip_custom_validation=True)

    def unarchive(self):
        """Unarchive the model instance."""
        self.archived = False
        self.archived_reason = ''
        self.archived_by = None
        self.archived_on = None
        self.save(skip_custom_validation=True)

    def get_datetime_fields(self):
        """Return list of fields that should be mapped as datetime."""
        fields = super().get_datetime_fields()
        return fields + ['archived_on']


class BaseConstantModel(models.Model):
    """Constant tables for FKs."""

    id = models.UUIDField(primary_key=True)
    name = models.TextField(blank=True)
    selectable = models.BooleanField(default=True)

    class Meta:  # noqa: D101
        abstract = True
        ordering = ('name', )

    def __str__(self):
        """Human readable admin name."""
        return self.name


class TaskInfo(models.Model):
    """Holds information about the tasks."""

    task_id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    db_table = models.CharField(max_length=100)
    update = models.BooleanField()
    changes = JSONField()
    manual_rerun_task = models.ForeignKey('self', null=True, blank=True)

    class Meta:  # noqa: D101
        verbose_name_plural = 'Task info'

    @property
    def async_result(self):
        """Return the result of the task."""
        return tasks.save_to_korben.AsyncResult(str(self.task_id))

    @property
    def status(self):
        """Handy shortcut to get the task status."""
        return self.async_result.status

    def __str__(self):
        """Return task UUID."""
        return str(self.task_id)
