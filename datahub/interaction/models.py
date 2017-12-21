import uuid

from django.conf import settings
from django.db import models
from model_utils import Choices

from datahub.core.models import BaseConstantModel, BaseModel
from datahub.core.utils import StrEnum

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class InteractionPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)
    """

    read_all = 'read_all_interaction'
    read_associated_investmentproject = 'read_associated_investmentproject_interaction'
    change_all = 'change_all_interaction'
    change_associated_investmentproject = 'change_associated_investmentproject_interaction'
    add_all = 'add_all_interaction'
    add_associated_investmentproject = 'add_associated_investmentproject_interaction'
    delete = 'delete_interaction'


class CommunicationChannel(BaseConstantModel):
    """Communication channel/mode of communication."""


class Interaction(BaseModel):
    """Interaction."""

    KINDS = Choices(
        ('interaction', 'Interaction'),
        ('service_delivery', 'Service delivery'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    kind = models.CharField(max_length=MAX_LENGTH, choices=KINDS)
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
    event = models.ForeignKey(
        'event.Event',
        related_name="%(class)ss",  # noqa: Q000
        blank=True,
        null=True,
        on_delete=models.SET_NULL
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
    communication_channel = models.ForeignKey(
        'CommunicationChannel', blank=True, null=True,
        on_delete=models.SET_NULL
    )
    investment_project = models.ForeignKey(
        'investment.InvestmentProject',
        related_name="%(class)ss",  # noqa: Q000
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this interaction.'
    )

    @property
    def is_event(self):
        """Whether this service delivery is for an event."""
        if self.kind == self.KINDS.service_delivery:
            return bool(self.event)
        return None

    def __str__(self):
        """Human-readable representation."""
        return self.subject

    class Meta:
        indexes = [
            models.Index(fields=['-date', '-created_on']),
        ]
        permissions = (
            (
                InteractionPermission.read_all,
                'Can read all interaction'
            ),
            (
                InteractionPermission.read_associated_investmentproject,
                'Can read interaction for associated investment projects'
            ),
            (
                InteractionPermission.add_associated_investmentproject,
                'Can add interaction for associated investment projects'
            ),
            (
                InteractionPermission.change_associated_investmentproject,
                'Can change interaction for associated investment projects'
            ),
        )
        default_permissions = (
            'add_all',
            'change_all',
            'delete',
        )
