import uuid

from django.conf import settings
from django.db import models

from datahub.core import reversion

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


# @reversion.register_base_model
class StovaEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    event_id = models.IntegerField(unique=True)
    url = models.TextField()

    city = models.TextField()
    code = models.CharField()

    name = models.TextField()

    state = models.TextField()
    country = models.CharField(max_length=MAX_LENGTH)

    max_reg = models.IntegerField(null=True)

    end_date = models.DateTimeField(null=True)

    timezone = models.CharField(max_length=MAX_LENGTH)
    folder_id = models.IntegerField(null=True)
    live_date = models.DateTimeField(null=True)
    close_date = models.DateTimeField(null=True)
    created_by = models.CharField(max_length=MAX_LENGTH)
    price_type = models.CharField(max_length=MAX_LENGTH)
    start_date = models.DateTimeField(null=True)
    description = models.TextField()
    modified_by = models.CharField(max_length=MAX_LENGTH)
    contact_info = models.CharField(max_length=MAX_LENGTH)
    created_date = models.DateTimeField()
    location_city = models.CharField(max_length=MAX_LENGTH)
    location_name = models.CharField(max_length=MAX_LENGTH)
    modified_date = models.DateTimeField()
    client_contact = models.CharField(max_length=MAX_LENGTH)
    location_state = models.CharField(max_length=MAX_LENGTH)
    default_language = models.CharField(max_length=MAX_LENGTH)
    location_country = models.CharField(max_length=MAX_LENGTH)
    approval_required = models.BooleanField()
    location_address1 = models.CharField(max_length=MAX_LENGTH)
    location_address2 = models.CharField(max_length=MAX_LENGTH)
    location_address3 = models.CharField(max_length=MAX_LENGTH)
    location_postcode = models.CharField(max_length=MAX_LENGTH)
    standard_currency = models.CharField(max_length=MAX_LENGTH)
