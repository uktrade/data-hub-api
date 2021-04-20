import uuid

from django.conf import settings
from django.db import models
from mptt.fields import TreeForeignKey

from datahub.core import reversion
from datahub.core.models import BaseConstantModel, BaseModel, DisableableModel
from datahub.core.utils import get_front_end_url

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class Event(BaseModel, DisableableModel):
    """An event (exhibition etc.)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=MAX_LENGTH)
    event_type = models.ForeignKey('EventType', on_delete=models.deletion.PROTECT)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location_type = models.ForeignKey(
        'LocationType',
        on_delete=models.deletion.SET_NULL,
        null=True,
        blank=True,
    )
    address_1 = models.CharField(max_length=MAX_LENGTH)
    address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_town = models.CharField(max_length=MAX_LENGTH)
    address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_country = models.ForeignKey(
        'metadata.Country',
        on_delete=models.PROTECT,
        related_name='+',
    )
    uk_region = models.ForeignKey(
        'metadata.UKRegion',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    notes = models.TextField(blank=True)
    organiser = models.ForeignKey(
        'company.Advisor',
        on_delete=models.deletion.PROTECT,
        null=True,
        blank=True,
    )
    lead_team = models.ForeignKey(
        'metadata.Team',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
    )
    teams = models.ManyToManyField('metadata.Team', blank=True, related_name='+')
    has_related_trade_agreements = models.BooleanField(null=True, blank=True)
    related_trade_agreements = models.ManyToManyField('metadata.TradeAgreement', blank=True)
    related_programmes = models.ManyToManyField('Programme', blank=True)
    service = TreeForeignKey(
        'metadata.Service',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this event.',
    )

    class Meta:
        indexes = [
            # For datasets app which includes API endpoints to be consumed by data-flow
            models.Index(fields=('created_on', 'id')),
        ]

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    def __str__(self):
        """Human-readable representation"""
        return self.name


class Programme(BaseConstantModel):
    """Related programmes for events."""


class EventType(BaseConstantModel):
    """Event types."""


class LocationType(BaseConstantModel):
    """Location types for events."""
