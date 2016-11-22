from dateutil import parser
from django.conf import settings
from django.db import models
from django.utils.timezone import now

from datahub.core.mixins import DeferredSaveModelMixin


class BaseModel(DeferredSaveModelMixin, models.Model):
    """Common fields for most of the models we use."""

    archived = models.BooleanField(default=False)
    archived_on = models.DateTimeField(null=True)
    archived_reason = models.TextField(blank=True, null=True)
    archived_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    created_on = models.DateTimeField(null=True, blank=True)
    modified_on = models.DateTimeField(null=True, blank=True)

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

    def clean(self):
        """Custom validation for created_on and modified_on.

        If the fields are empty, populate them.
        """
        super().clean()
        self.created_on = self.created_on if self.created_on else now()
        self.modified_on = self.modified_on if self.modified_on else now()

    def _map_korben_response_to_model_instance(self, korben_response):
        """Handle date time object."""
        super(BaseModel, self)._map_korben_response_to_model_instance(korben_response)
        archived_on = korben_response.json().get('archived_on')
        modified_on = korben_response.json().get('modified_on')
        created_on = korben_response.json().get('created_on')

        self.archived_on = parser.parse(archived_on) if archived_on else archived_on
        self.modified_on = parser.parse(modified_on) if modified_on else modified_on
        self.created_on = parser.parse(created_on) if created_on else created_on


class BaseConstantModel(models.Model):
    """Constant tables for FKs."""

    id = models.UUIDField(primary_key=True)
    name = models.TextField(blank=True)

    class Meta:  # noqa: D101
        abstract = True
        ordering = ('name', )

    def __str__(self):
        """Humand readable admin name."""
        return self.name
