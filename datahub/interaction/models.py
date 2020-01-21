import uuid

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from model_utils import Choices
from mptt.fields import TreeForeignKey

from datahub.company.models import CompanyExportCountry
from datahub.core import reversion
from datahub.core.models import (
    ArchivableModel,
    BaseConstantModel,
    BaseModel,
    BaseOrderedConstantModel,
)
from datahub.core.utils import get_front_end_url, StrEnum
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class InteractionPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)


    The following codenames mean that the user can view, change, add or delete any type of
    interaction:

    view_all_interaction
    change_all_interaction
    add_all_interaction
    delete_interaction


    The following codenames mean that the user can only view, change and add interactions for
    investment projects that they are associated with:

    view_associated_investmentproject_interaction
    change_associated_investmentproject_interaction
    add_associated_investmentproject_interaction

    They cannot view, change or add interactions that do not relate to an investment project.

    An associated project has the same meaning that it does in investment projects (that is a
    project that was created by an adviser in the same team, or an adviser in the same team has
    been linked to the project).


    Note that permissions on other models are independent of permissions on interactions. Also
    note that if both *_all_* and *_associated_investmentproject_* permissions are assigned to the
    same user,  the *_all_* permission will be the effective one.
    """

    view_all = 'view_all_interaction'
    view_associated_investmentproject = 'view_associated_investmentproject_interaction'
    change_all = 'change_all_interaction'
    change_associated_investmentproject = 'change_associated_investmentproject_interaction'
    add_all = 'add_all_interaction'
    add_associated_investmentproject = 'add_associated_investmentproject_interaction'
    delete = 'delete_interaction'
    export = 'export_interaction'


class CommunicationChannel(BaseConstantModel):
    """Communication channel/mode of communication."""


class ServiceDeliveryStatus(BaseOrderedConstantModel):
    """
    Status of a service delivery.

    Primarily used for Tradeshow Access Programme (TAP) grants.
    """


class PolicyArea(BaseOrderedConstantModel):
    """
    Policy area for a policy feedback interaction.
    """


class PolicyIssueType(BaseOrderedConstantModel):
    """
    Policy issue type for a policy feedback interaction.
    """


class InteractionDITParticipant(models.Model):
    """
    Many-to-many model between an interaction and an adviser (called a DIT participant).

    Due to a small number of old records that have only a team or an adviser,
    adviser and team are nullable (but do not have blank=True, to avoid any further
    such records being created).
    """

    id = models.BigAutoField(primary_key=True)
    interaction = models.ForeignKey(
        'interaction.Interaction',
        on_delete=models.CASCADE,
        related_name='dit_participants',
    )
    adviser = models.ForeignKey(
        'company.Advisor',
        null=True,
        on_delete=models.CASCADE,
        related_name='+',
    )
    team = models.ForeignKey(
        'metadata.Team',
        null=True,
        on_delete=models.CASCADE,
        related_name='+',
    )

    def __str__(self):
        """Human-readable representation."""
        return f'{self.interaction} – {self.adviser} – {self.team}'

    class Meta:
        default_permissions = ()
        unique_together = (('interaction', 'adviser'),)


class ServiceQuestion(BaseOrderedConstantModel):
    """Service question model."""

    service = TreeForeignKey(
        'metadata.Service',
        related_name='interaction_questions',
        on_delete=models.PROTECT,
    )


class ServiceAnswerOption(BaseOrderedConstantModel):
    """Service answer option model."""

    question = models.ForeignKey(
        'interaction.ServiceQuestion',
        related_name='answer_options',
        on_delete=models.CASCADE,
    )


class ServiceAdditionalQuestion(BaseOrderedConstantModel):
    """Service additional question model."""

    class Type(models.TextChoices):
        TEXT = ('text', 'Text')
        MONEY = ('money', 'Money')

    type = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=Type.choices,
    )

    is_required = models.BooleanField(default=False)

    answer_option = models.ForeignKey(
        'interaction.ServiceAnswerOption',
        related_name='additional_questions',
        on_delete=models.CASCADE,
    )


@reversion.register_base_model()
class Interaction(ArchivableModel, BaseModel):
    """Interaction."""

    KINDS = Choices(
        ('interaction', 'Interaction'),
        ('service_delivery', 'Service delivery'),
    )

    STATUSES = Choices(
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    )

    THEMES = Choices(
        (None, 'Not set'),
        ('export', 'Export'),
        ('investment', 'Investment'),
        ('other', 'Something else'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    theme = models.CharField(
        max_length=MAX_LENGTH,
        choices=THEMES,
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=MAX_LENGTH, choices=KINDS)
    status = models.CharField(
        max_length=MAX_LENGTH,
        choices=STATUSES,
        default=STATUSES.complete,
    )
    # Set if the interaction was imported from an external source
    # (e.g. an .ics (iCalendar) file or a CSV file).
    #
    # Examples
    #
    # Imported from a CSV file via the import interactions tool in the admin site:
    #
    # {
    #     "file": {
    #         "name": "<file name>",
    #         "size": <file size in bytes>,
    #         "sha256": "<SHA-256 hash>"
    #     }
    # }
    source = JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    date = models.DateTimeField()
    company = models.ForeignKey(
        'company.Company',
        related_name='%(class)ss',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    contacts = models.ManyToManyField(
        'company.Contact',
        related_name='%(class)ss',
        blank=True,
    )
    event = models.ForeignKey(
        'event.Event',
        related_name='%(class)ss',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='For service deliveries only.',
    )
    service = TreeForeignKey(
        'metadata.Service',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    service_answers = JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)

    subject = models.TextField()
    notes = models.TextField(max_length=10000, blank=True)
    communication_channel = models.ForeignKey(
        'CommunicationChannel', blank=True, null=True,
        on_delete=models.SET_NULL,
        help_text='For interactions only.',
    )
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this '
                  'interaction.',
    )
    service_delivery_status = models.ForeignKey(
        'ServiceDeliveryStatus', blank=True, null=True, on_delete=models.PROTECT,
        verbose_name='status',
        help_text='For service deliveries only.',
    )
    # Investments
    investment_project = models.ForeignKey(
        'investment.InvestmentProject',
        related_name='%(class)ss',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='For interactions only.',
    )
    # Grants
    grant_amount_offered = models.DecimalField(
        null=True, blank=True, max_digits=19, decimal_places=2,
        help_text='For service deliveries only.',
    )
    net_company_receipt = models.DecimalField(
        null=True, blank=True, max_digits=19, decimal_places=2,
        help_text='For service deliveries only.',
    )
    # Policy feedback
    was_policy_feedback_provided = models.BooleanField()
    policy_areas = models.ManyToManyField(
        'PolicyArea',
        blank=True,
        related_name='interactions',
    )
    policy_issue_types = models.ManyToManyField(
        'PolicyIssueType',
        blank=True,
        related_name='interactions',
    )
    policy_feedback_notes = models.TextField(blank=True, default='')

    were_countries_discussed = models.BooleanField(null=True)

    @property
    def is_event(self):
        """Whether this service delivery is for an event."""
        if self.kind == self.KINDS.service_delivery:
            return bool(self.event)
        return None

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    def __str__(self):
        """Human-readable representation."""
        return self.subject

    class Meta:
        indexes = [
            models.Index(fields=['-date', '-created_on']),
            # For the list of a user's personal companies (displayed on the Data Hub home page)
            models.Index(fields=['company', '-date', '-created_on', 'id']),
            # For activity-stream
            models.Index(fields=['modified_on', 'id']),
            # For meeting update lookups
            GinIndex(fields=['source']),
            # For datasets app which includes API endpoints to be consumed by data-flow
            models.Index(fields=('created_on', 'id')),
        ]
        permissions = (
            (
                InteractionPermission.view_associated_investmentproject.value,
                'Can view interaction for associated investment projects',
            ),
            (
                InteractionPermission.add_associated_investmentproject.value,
                'Can add interaction for associated investment projects',
            ),
            (
                InteractionPermission.change_associated_investmentproject.value,
                'Can change interaction for associated investment projects',
            ),
            (
                InteractionPermission.export.value,
                'Can export interaction',
            ),
        )
        default_permissions = (
            'add_all',
            'change_all',
            'delete',
            'view_all',
        )


@reversion.register_base_model()
class InteractionExportCountry(BaseModel):
    """
    Record `Interaction`'s exporting status to a `Country`.
    Where `Status` is `CompanyExportCountry.EXPORT_INTEREST_STATUSES`

    This data will help consolidate company level countries
    in `company.CompanyExportCountry`
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )
    country = models.ForeignKey(
        metadata_models.Country,
        on_delete=models.PROTECT,
        related_name='interaction_discussed',
    )
    interaction = models.ForeignKey(
        Interaction,
        on_delete=models.CASCADE,
        related_name='export_countries',
    )
    status = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=CompanyExportCountry.EXPORT_INTEREST_STATUSES,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['country', 'interaction'],
                name='unique_country_interaction',
            ),
        ]
        verbose_name_plural = 'interaction export countries'

    def __str__(self):
        """
        Admin human readable name
        """
        return (
            f'{self.interaction} {self.country} {self.status}'
        )
