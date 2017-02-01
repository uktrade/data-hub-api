import uuid

from django.db import models

from datahub.core.mixins import KorbenSaveModelMixin
from datahub.core.models import ArchivableModel, BaseModel


class InteractionAbstract(KorbenSaveModelMixin, ArchivableModel, BaseModel):
    """Common fields for all interaction flavours."""

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    date = models.DateTimeField()
    company = models.ForeignKey(
        'company.Company',
        related_name="%(class)ss",  # noqa: Q000
    )
    contact = models.ForeignKey(
        'company.Contact',
        related_name="%(class)ss",  # noqa: Q000
    )
    service = models.ForeignKey('metadata.Service')
    subject = models.TextField()
    dit_advisor = models.ForeignKey(
        'company.Advisor',
        related_name="%(class)ss",  # noqa: Q000
    )
    notes = models.TextField()

    class Meta:  # noqa: D101
        abstract = True

    def __str__(self):
        """Admin displayed human readable name."""
        return self.subject

    def get_datetime_fields(self):
        """Return list of fields that should be mapped as datetime."""
        return super().get_datetime_fields() + ['date']


class Interaction(InteractionAbstract):
    """Interaction."""

    interaction_type = models.ForeignKey('metadata.InteractionType')
    dit_team = models.ForeignKey('metadata.Team')

    def get_excluded_fields(self):
        """Don't send user to Korben, it's a Django thing."""
        return ['user']
