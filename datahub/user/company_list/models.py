from uuid import uuid4

from django.conf import settings
from django.db import models

from datahub.core.models import BaseModel
from datahub.core.utils import StrEnum


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
