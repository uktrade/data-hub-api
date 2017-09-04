import uuid

from django.conf import settings
from django.db import models
from model_utils import Choices

from datahub.core.models import BaseConstantModel, BaseModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Event(BaseModel):
    """An event (exhibition etc.)"""

    EVENT_TYPES = Choices(
        ('Seminar', 'seminar', 'Seminar'),
        ('Exhibition', 'exhibition', 'Exhibition'),
        ('Inward mission', 'inward_mission', 'Inward mission'),
        ('Outward mission', 'outward_mission', 'Outward mission'),
        ('UK region local service', 'uk_region_local_service', 'UK region local service'),
    )

    LOCATION_TYPES = Choices(
        ('HQ', 'hq', 'HQ'),
        ('Post', 'post', 'Post'),
        ('Regional network', 'regional_network', 'Regional network'),
        ('Other', 'other', 'Other'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=MAX_LENGTH)
    event_type = models.CharField(max_length=MAX_LENGTH, choices=EVENT_TYPES)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location_type = models.CharField(max_length=MAX_LENGTH, blank=True, choices=LOCATION_TYPES)
    address_1 = models.CharField(max_length=MAX_LENGTH)
    address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_town = models.CharField(max_length=MAX_LENGTH)
    address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH)
    address_country = models.ForeignKey(
        'metadata.Country', on_delete=models.PROTECT, related_name='+'
    )
    notes = models.TextField(blank=True)
    lead_team = models.ForeignKey(
        'metadata.Team', on_delete=models.PROTECT, null=True, blank=True, related_name='+'
    )
    additional_teams = models.ManyToManyField('metadata.Team', blank=True, related_name='+')
    related_programmes = models.ManyToManyField('Programme', blank=True)

    def __str__(self):
        """Human-readable representation"""
        return self.name


class Programme(BaseConstantModel):
    """Related programmes for events."""
