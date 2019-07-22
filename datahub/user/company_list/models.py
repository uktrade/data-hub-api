from uuid import uuid4

from django.db import models

from datahub.core.models import BaseModel
from datahub.core.utils import StrEnum


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
    adviser = models.ForeignKey('company.Advisor', on_delete=models.CASCADE)
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('adviser', 'company'),
                name='unique_adviser_and_company',
            ),
        ]
        indexes = [
            models.Index(fields=('adviser', 'company')),
        ]
