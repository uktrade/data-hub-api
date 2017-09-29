import uuid

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from model_utils import Choices

from datahub.core.models import BaseModel


class Interaction(BaseModel):
    """Interaction."""

    KINDS = Choices(
        ('interaction', 'Interaction'),
        ('service_delivery', 'Service delivery'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    kind = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH, choices=KINDS)
    date = models.DateTimeField()
    company = models.ForeignKey(
        'company.Company',
        related_name="%(class)ss",  # noqa: Q000
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    contact = models.ForeignKey(
        'company.Contact',
        related_name="%(class)ss",  # noqa: Q000
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    service = models.ForeignKey(
        'metadata.Service', blank=True, null=True, on_delete=models.SET_NULL
    )
    subject = models.TextField()
    dit_adviser = models.ForeignKey(
        'company.Advisor',
        related_name="%(class)ss",  # noqa: Q000
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    notes = models.TextField(max_length=settings.CDMS_TEXT_MAX_LENGTH)
    dit_team = models.ForeignKey(
        'metadata.Team', blank=True, null=True, on_delete=models.SET_NULL
    )
    interaction_type = models.ForeignKey(
        'metadata.InteractionType', blank=True, null=True,
        on_delete=models.SET_NULL
    )
    investment_project = models.ForeignKey(
        'investment.InvestmentProject',
        related_name="%(class)ss",  # noqa: Q000
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        """Human-readable representation."""
        return self.subject

    class Meta:  # noqa: D101
        indexes = [
            models.Index(fields=['-date', '-created_on']),
        ]


class ServiceOffer(models.Model):
    """
    Service offer.

    Deprecated.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    service = models.ForeignKey('metadata.Service', on_delete=models.CASCADE)
    dit_team = models.ForeignKey(
        'metadata.Team', blank=True, null=True, on_delete=models.CASCADE
    )
    event = models.ForeignKey(
        'metadata.Event', blank=True, null=True, on_delete=models.CASCADE
    )

    @cached_property
    def name(self):
        """Generate name."""
        name_elements = [
            getattr(self, key).name
            for key in ['service', 'dit_team', 'event'] if getattr(self, key) is not None]
        return ' : '.join(name_elements)

    def __str__(self):
        """Human readable object name."""
        return self.name


class ServiceDelivery(BaseModel):
    """
    Service delivery.

    Deprecated.
    """

    ENTITY_NAME = 'ServiceDelivery'
    API_MAPPING = {
        ('company', 'Company'),
        ('contact', 'Contact'),
        ('country_of_interest', 'Country'),
        ('dit_adviser', 'Adviser'),
        ('dit_team', 'Team'),
        ('sector', 'Sector'),
        ('service', 'Service'),
        ('status', 'ServiceDeliveryStatus'),
        ('uk_region', 'UKRegion'),
        ('service_offer', 'ServiceOffer'),
        ('event', 'Event')
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    date = models.DateTimeField()
    company = models.ForeignKey(
        'company.Company',
        related_name="%(class)ss",  # noqa: Q000
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    contact = models.ForeignKey(
        'company.Contact',
        related_name="%(class)ss",  # noqa: Q000
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    service = models.ForeignKey(
        'metadata.Service', blank=True, null=True, on_delete=models.SET_NULL
    )
    subject = models.TextField()
    dit_adviser = models.ForeignKey(
        'company.Advisor',
        related_name="%(class)ss",  # noqa: Q000
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    notes = models.TextField(max_length=settings.CDMS_TEXT_MAX_LENGTH)
    dit_team = models.ForeignKey(
        'metadata.Team', blank=True, null=True, on_delete=models.SET_NULL
    )
    status = models.ForeignKey(
        'metadata.ServiceDeliveryStatus', on_delete=models.PROTECT
    )
    service_offer = models.ForeignKey(
        ServiceOffer, blank=True, null=True, on_delete=models.SET_NULL
    )
    uk_region = models.ForeignKey(
        'metadata.UKRegion', blank=True, null=True, on_delete=models.SET_NULL
    )
    sector = models.ForeignKey(
        'metadata.Sector', blank=True, null=True, on_delete=models.SET_NULL
    )
    country_of_interest = models.ForeignKey(
        'metadata.Country', blank=True, null=True, on_delete=models.SET_NULL
    )
    feedback = models.TextField(
        max_length=settings.CDMS_TEXT_MAX_LENGTH, blank=True, null=True
    )
    event = models.ForeignKey(
        'metadata.Event', blank=True, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        """Human-readable representation."""
        return self.subject

    def clean(self):
        """Custom validation."""
        if self.service_offer and not self.event:
            self.event = self.service_offer.event
        super().clean()

    class Meta:  # noqa: D101
        verbose_name_plural = 'service deliveries'
