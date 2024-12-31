import uuid

from django.conf import settings
from django.db import models

from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.core import reversion


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class StovaAttendee(models.Model):
    """
    Stova can also be known as Aventri.
    This model is filled and based off data from the S3 bucket: ExportAventriAttendees.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    stova_attendee_id = models.IntegerField(unique=True)
    stova_event_id = models.IntegerField(unique=True)

    created_by = models.CharField(max_length=MAX_LENGTH)
    created_date = models.DateTimeField()
    modified_by = models.CharField(max_length=MAX_LENGTH)
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

    # Data Hub Fields
    created_on = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='stova_attendee',
        help_text='If a company match can be found from company_name, the relation is added.',
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='stova_attendee',
        help_text='If a contact match can be found from the email, the relation is added.',
    )
