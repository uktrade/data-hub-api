import uuid

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from datahub.core.models import BaseModel


class InteractionAbstract(BaseModel):
    """Common fields for all interaction flavours."""

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

    class Meta:  # noqa: D101
        abstract = True

    def __str__(self):
        """Admin displayed human readable name."""
        return self.subject


class Interaction(InteractionAbstract):
    """Interaction."""

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

    class Meta:  # noqa: D101
        permissions = (
            ('view_interaction', 'Can view interaction'),
        )


class ServiceOffer(models.Model):
    """Service offer."""

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

    class Meta:  # noqa: D101
        permissions = (
            ('view_serviceoffer', 'Can view service offer'),
        )


class ServiceDelivery(InteractionAbstract):
    """Service delivery."""

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

    def clean(self):
        """Custom validation."""
        if self.service_offer and not self.event:
            self.event = self.service_offer.event
        super().clean()

    class Meta(InteractionAbstract.Meta):  # noqa: D101
        verbose_name_plural = 'service deliveries'
        permissions = (
            ('view_servicedelivery', 'Can view service delivery'),
        )
