import uuid

from django.conf import settings
from django.db import models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class StovaEvent(models.Model):
    """
    Stova can also be known as Aventri.

    This model is filled and based off data from the S3 bucket: AventriEvents
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    event_id = models.IntegerField(unique=True)
    name = models.TextField()
    description = models.TextField()
    code = models.CharField()

    created_by = models.CharField(max_length=MAX_LENGTH)
    modified_by = models.CharField(max_length=MAX_LENGTH)

    client_contact = models.CharField(max_length=MAX_LENGTH)
    contact_info = models.CharField(max_length=MAX_LENGTH)

    country = models.CharField(max_length=MAX_LENGTH)
    city = models.TextField()
    state = models.TextField()
    timezone = models.CharField(max_length=MAX_LENGTH)
    url = models.TextField()
    max_reg = models.IntegerField(null=True)

    created_date = models.DateTimeField()
    modified_date = models.DateTimeField()
    start_date = models.DateTimeField(null=True)
    live_date = models.DateTimeField(null=True)
    close_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

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
    folder_id = models.IntegerField(null=True)
    default_language = models.CharField(max_length=MAX_LENGTH)
    standard_currency = models.CharField(max_length=MAX_LENGTH)
