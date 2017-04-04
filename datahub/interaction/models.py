import uuid

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
    notes = models.TextField(max_length=4000)  # CDMS limit
    dit_team = models.ForeignKey('metadata.Team')

    class Meta:  # noqa: D101
        abstract = True

    def __str__(self):
        """Admin displayed human readable name."""
        return self.subject


class Interaction(InteractionAbstract):
    """Interaction."""

    interaction_type = models.ForeignKey('metadata.InteractionType')


class ServiceOffer(models.Model):
    """Service offer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    service = models.ForeignKey('metadata.Service')
    dit_team = models.ForeignKey('metadata.Team')
    event = models.ForeignKey('metadata.Event', null=True, blank=True)

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


class ServiceDelivery(InteractionAbstract):
    """Service delivery."""

    ENTITY_NAME = 'ServiceDelivery'
    API_MAPPING = {
        ('company', 'Company'),
        ('contact', 'Contact'),
        ('country', 'Country'),
        ('dit_advisor', 'Advisor'),
        ('dit_team', 'Team'),
        ('sector', 'Sector'),
        ('service', 'Service'),
        ('status', 'ServiceDeliveryStatus'),
        ('uk_region', 'UKRegion'),
        ('service_offer', 'ServiceOffer')
    }

    status = models.ForeignKey('metadata.ServiceDeliveryStatus')
    service_offer = models.ForeignKey(ServiceOffer, null=True, blank=True)
    uk_region = models.ForeignKey('metadata.UKRegion', null=True, blank=True)
    sector = models.ForeignKey('metadata.Sector', null=True, blank=True)
    country_of_interest = models.ForeignKey('metadata.Country', null=True, blank=True)
    feedback = models.TextField(max_length=4000, blank=True)  # CDMS limit
    event = models.ForeignKey('metadata.Event', null=True, blank=True)

    def clean(self):
        """Custom validation."""
        if self.service_offer and not self.event:
            self.event = self.service_offer.event
        super().clean()
