import uuid

from django.conf import settings
from django.db import models


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class StovaAttendee(models.Model):
    """
    Stova can also be known as Aventri.
    This model is filled and based off data from the S3 bucket: ExportAventriAttendees
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    stova_event_id = models.IntegerField(unique=True)

    created_by = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField()
    modified_by = models.IntegerField(null=True, blank=True)
    modified_date = models.DateTimeField()

    email = models.CharField(max_length=MAX_LENGTH)
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    attendee_questions = models.CharField(max_length=MAX_LENGTH)

    company_name = models.CharField(max_length=MAX_LENGTH)
    category = models.CharField(max_length=MAX_LENGTH)
    registration_status = models.CharField(max_length=MAX_LENGTH)

    virtual_event_attendance = models.CharField(max_length=MAX_LENGTH)
    language = models.CharField(max_length=MAX_LENGTH)

    last_lobby_login = models.DateTimeField()
