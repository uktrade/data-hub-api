from uuid import uuid4

from django.conf import settings
from django.db import models

from datahub.core import reversion
from datahub.core.models import ArchivableModel, BaseModel
from datahub.core.utils import StrEnum
from datahub.metadata import models as metadata_models


class CompanyList(BaseModel):
    """
    A user-created list of companies.

    (List contents are stored in the separate CompanyListItem model.)
    """

    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    adviser = models.ForeignKey(
        'company.Advisor',
        on_delete=models.CASCADE,
        related_name='company_lists',
    )

    def __str__(self):
        """Human-friendly representation."""
        return f'{self.name} – {self.adviser}'


class CompanyListItemPermissionCode(StrEnum):
    """CompanyListItem permission codename constants."""

    view_company_list_item = 'view_companylistitem'
    add_company_list_item = 'add_companylistitem'
    change_company_list_item = 'change_companylistitem'
    delete_company_list_item = 'delete_companylistitem'


class CompanyListItem(BaseModel):
    """
    An item on a user's personal list of companies.

    Each company can appear only once for a particular user.

    Note that the primary key is not exposed via the API.
    """

    id = models.UUIDField(primary_key=True, default=uuid4)
    list = models.ForeignKey(CompanyList, models.CASCADE, related_name='items')
    company = models.ForeignKey(
        'company.Company',
        on_delete=models.CASCADE,
        related_name='company_list_items',
    )

    def __str__(self):
        """Human-friendly representation."""
        return f'{self.company} – {self.list}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('list', 'company'),
                name='unique_list_and_company',
            ),
        ]


@reversion.register_base_model()
class PipelineItem(ArchivableModel, BaseModel):
    """
    Model holding pipeline list items.
    """

    class Status(models.TextChoices):
        LEADS = ('leads', 'Leads')
        IN_PROGRESS = ('in_progress', 'In progress')
        WIN = ('win', 'Win')

    class LikelihoodToWin(models.IntegerChoices):
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    id = models.UUIDField(primary_key=True, default=uuid4)
    company = models.ForeignKey(
        'company.Company',
        on_delete=models.CASCADE,
        related_name='pipeline_list_items',
    )
    adviser = models.ForeignKey(
        'company.Advisor',
        on_delete=models.CASCADE,
        help_text='Owner of the pipeline item',
    )
    status = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=Status.choices,
        help_text='Item status within the pipeline',
    )
    name = models.CharField(
        blank=True,
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        help_text='Name to represent the item within the pipeline',
    )
    contacts = models.ManyToManyField(
        'company.Contact',
        blank=True,
        related_name='pipeline_items_m2m',
        help_text='Preferred company contacts',
    )
    sector = models.ForeignKey(
        metadata_models.Sector, blank=True, null=True,
        on_delete=models.SET_NULL,
        help_text='Sector in which the proposal is being worked on',
    )
    potential_value = models.DecimalField(
        blank=True, null=True, max_digits=19, decimal_places=0,
        help_text='Potential value (£) of the proposal',
    )
    likelihood_to_win = models.IntegerField(
        blank=True, null=True,
        choices=LikelihoodToWin.choices,
        help_text='How likely the user thinks this proposal will result in success',
    )
    expected_win_date = models.DateField(
        blank=True, null=True,
        help_text='Approximate expected date for this proposal to succeed',
    )

    def __str__(self):
        """Human-friendly representation."""
        return f'{self.company} - {self.name} - {self.status}'
