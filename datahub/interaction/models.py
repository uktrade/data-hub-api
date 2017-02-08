import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property

from datahub.core.mixins import KorbenSaveModelMixin
from datahub.core.models import BaseModel


class InteractionAbstract(KorbenSaveModelMixin, BaseModel):
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

    FIELDS_THAT_SHOULD_NOT_ALLOW_UNDEFS = (
        'dit_advisor', 'dit_team', 'service', 'interaction_type',
    )

    interaction_type = models.ForeignKey('metadata.InteractionType')
    dit_team = models.ForeignKey('metadata.Team')

    def clean(self):
        """Custom validation."""
        super().clean()

        for field in self.FIELDS_THAT_SHOULD_NOT_ALLOW_UNDEFS:
            value = getattr(self, field + '_id')
            if str(value) == '0167b456-0ddd-49bd-8184-e3227a0b6396':  # Undefined
                raise ValidationError(message={
                    field: ['This field is required'],
                })


class ServiceOffer(models.Model):
    """Service offer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    dit_team = models.ForeignKey('metadata.Team')
    service = models.ForeignKey('metadata.Service')

    @cached_property
    def name(self):
        """Generate name."""
        return '{0} : {1}'.format(self.service.name, self.dit_team.name)

    def __str__(self):
        """Human readable object name."""
        return self.name


class ServiceDelivery(InteractionAbstract):
    """Service delivery."""

    status = models.ForeignKey('metadata.ServiceDeliveryStatus')
    service_offer = models.ForeignKey(ServiceOffer, null=True, blank=True)
    dit_team = models.ForeignKey('metadata.Team')
    uk_region = models.ForeignKey('metadata.UKRegion', null=True, blank=True)
    sector = models.ForeignKey('metadata.Sector', null=True, blank=True)
    country_of_interest = models.ForeignKey('metadata.Country', null=True, blank=True)
    feedback = models.TextField(max_length=4000, blank=True)  # CDMS limit

    def save(self, skip_custom_validation=False, **kwargs):
        """Add service offer."""
        service_offer, _ = ServiceOffer.objects.get_or_create(
            dit_team=self.dit_team,
            service=self.service
        )
        self.service_offer = service_offer
        super().save(skip_custom_validation=skip_custom_validation, **kwargs)
