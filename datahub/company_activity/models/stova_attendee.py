import uuid

from django.conf import settings
from django.db import models

from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.company_activity.models.stova_event import StovaEvent
from datahub.core import reversion

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class StovaAttendee(models.Model):
    """Stova can also be known as Aventri.
    This model is filled and based off data from the S3 bucket: ExportAventriAttendees.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    stova_attendee_id = models.IntegerField(unique=True)
    stova_event_id = models.IntegerField()

    created_by = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    modified_by = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    modified_date = models.DateTimeField(blank=True, null=True)

    email = models.CharField(max_length=MAX_LENGTH)
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    attendee_questions = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    company_name = models.CharField(max_length=MAX_LENGTH)
    category = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registration_status = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    virtual_event_attendance = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    language = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    last_lobby_login = models.DateTimeField(blank=True, null=True)

    # Data Hub Fields
    created_on = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stova_attendee',
        help_text='If a company match can be found from company_name, the relation is added.',
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stova_attendee',
        help_text='If a contact match can be found from the email, the relation is added.',
    )

    # The FK to the ingested Stova Event in Data Hub.
    ingested_stova_event = models.ForeignKey(
        StovaEvent,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='stova_attendee',
        help_text=(
            'Each attendee comes with a Stova Event ID which is stored as its raw value under '
            'stova_attendee_id. This field is the FK to the ingested Stova Event in Data Hub.',
        ),
    )


class TempRelationStorage(models.Model):
    """Temporary model to store the deleted IDs of companies, interactions and contacts created
    from Stova. This is so there is a way to roll these back if the deletion fails.

    This will be removed shortly after all these stova created relations are deleted.
    """

    model_name = models.CharField(max_length=MAX_LENGTH)
    object_id = models.CharField(max_length=MAX_LENGTH)
