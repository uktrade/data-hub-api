from django.db import transaction

from datahub.company.models import Company
from datahub.dnb_api.tasks import sync_company_with_dnb


class CompanyAlreadyDNBLinkedException(Exception):
    """
    An exception to raise when a Data Hub company has already been linked with
    a DNB company record.
    """


@transaction.atomic
def link_company_with_dnb(
    dh_company_id,
    duns_number,
    modified_by,
    update_descriptor='admin:link_company_with_dnb',
):
    """
    Given a Data Hub company ID and a duns number, save the company with this
    duns number and update it's record from D&B.
    """
    company = Company.objects.get(id=dh_company_id)
    if company.duns_number:
        raise CompanyAlreadyDNBLinkedException(
            f'Company {company.id} is already linked with duns number {company.duns_number}',
        )
    company.duns_number = duns_number
    company.modified_by = modified_by
    company.save()
    sync_company_with_dnb.apply(
        args=(company.id,),
        kwargs={'update_descriptor': update_descriptor},
        throw=True,
    )
    company.refresh_from_db()
    return company
