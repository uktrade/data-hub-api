import uuid

from django.conf import settings
from django.db import models, transaction

from datahub.event.models import Event, EventType
from datahub.metadata.utils import get_country_by_country_name

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class StovaEvent(models.Model):
    """
    Stova can also be known as Aventri.

    This model is filled and based off data from the S3 bucket: ExportAventriEvents
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    stova_event_id = models.IntegerField(unique=True)
    name = models.TextField()
    description = models.TextField()
    code = models.CharField(max_length=MAX_LENGTH)

    created_by = models.IntegerField(null=True, blank=True)
    modified_by = models.IntegerField(null=True, blank=True)

    client_contact = models.IntegerField(null=True, blank=True)
    contact_info = models.CharField(max_length=MAX_LENGTH)

    country = models.CharField(max_length=MAX_LENGTH)
    city = models.CharField(max_length=MAX_LENGTH)
    state = models.CharField(max_length=MAX_LENGTH)
    timezone = models.CharField(max_length=MAX_LENGTH)
    url = models.TextField()
    max_reg = models.IntegerField(null=True, blank=True)

    created_date = models.DateTimeField()
    modified_date = models.DateTimeField()
    start_date = models.DateTimeField(null=True, blank=True)
    live_date = models.DateTimeField(null=True, blank=True)
    close_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    location_state = models.CharField(max_length=MAX_LENGTH)
    location_country = models.CharField(max_length=MAX_LENGTH)
    location_address1 = models.CharField(max_length=MAX_LENGTH)
    location_address2 = models.CharField(max_length=MAX_LENGTH)
    location_address3 = models.CharField(max_length=MAX_LENGTH)
    location_city = models.CharField(max_length=MAX_LENGTH)
    location_name = models.CharField(max_length=MAX_LENGTH)
    location_postcode = models.CharField(max_length=MAX_LENGTH)

    approval_required = models.BooleanField()
    price_type = models.CharField(max_length=MAX_LENGTH)
    folder_id = models.IntegerField(null=True, blank=True)
    default_language = models.CharField(max_length=MAX_LENGTH)
    standard_currency = models.CharField(max_length=MAX_LENGTH)

    def save(self, *args, **kwargs) -> None:
        """Overwritten to create/update a DataHub event from data in a Stova Event."""
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.create_or_update_datahub_event()

    def create_or_update_datahub_event(self) -> Event:
        # Dates are converted from string to datetime after saving, so refresh self otherwise
        # dates will still be string.
        # https://docs.djangoproject.com/en/4.2/ref/models/instances/#what-happens-when-you-save
        self.refresh_from_db()
        event, _ = Event.objects.update_or_create(
            stova_event_id=self.id,
            defaults={
                'name': self.name,
                'event_type_id': self.get_or_create_stova_event_type().id,
                'start_date': self.start_date.date() if self.start_date else '',
                'end_date': self.end_date.date() if self.end_date else '',
                'address_1': self.location_address1,
                'address_2': self.location_address2,
                'address_town': self.location_city,
                'address_county': self.location_state,
                'address_postcode': self.location_postcode,
                'address_country': get_country_by_country_name(self.name, 'GB'),
                'notes': self.description,
            },
        )
        return event

    @staticmethod
    def get_or_create_stova_event_type() -> EventType:
        """
        Returns or creates an `EventType`.

        DataHub events require an event type which is not provided by Stova. Therefore, all events
        ingested from Stova will be given the below event type by default.
        """
        event_type, _ = EventType.objects.get_or_create(
            name='Stova - unknown event type',
        )
        return event_type
