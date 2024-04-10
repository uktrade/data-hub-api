from decimal import Decimal

from django.db.models.query import QuerySet

from datahub.company.test.factories import (
    ArchivedCompanyFactory,
    CompanyFactory,
    CompanyWithAreaFactory,
    DuplicateCompanyFactory,
    SubsidiaryFactory,
)

from ..utils import (
    random_object_from_queryset,
    send_heartbeat_every_10_iterations,
)


COMPANY_TYPE_RATIOS = {
    'company': Decimal('0.5'),
    'company_with_area': Decimal('0.1'),
    'subsidiary_company': Decimal('0.2'),
    'archived_company': Decimal('0.1'),
    'duplicate_company': Decimal('0.1'),    
}


def generate_companies(
    number_of_companies: int,
    advisers: list[QuerySet],
):
    if sum(COMPANY_TYPE_RATIOS.values()) > 1:
        raise ValueError('Company type ratios must add up to 1')
    
    companies_per_adviser = number_of_companies // advisers.count()

    # Handle case when requested number is too small
    if number_of_companies < 10:
        for index, adviser in enumerate(advisers[:number_of_companies]):
            CompanyFactory(
                created_by=adviser,
                modified_by=adviser,
            )
        print(f'Generated {number_of_companies} companies')  # noqa
        return

    # Determine ratios
    n_companies = round(companies_per_adviser * COMPANY_TYPE_RATIOS['company'])
    n_companies_with_area = round(companies_per_adviser * COMPANY_TYPE_RATIOS['company_with_area'])
    n_subsidiary_companies = round(companies_per_adviser * COMPANY_TYPE_RATIOS['subsidiary_company'])
    n_archived_companies = round(companies_per_adviser * COMPANY_TYPE_RATIOS['archived_company'])
    n_duplicate_companies = round(companies_per_adviser * COMPANY_TYPE_RATIOS['duplicate_company'])

    companies = []
    for index, adviser in enumerate(advisers):
        companies.extend(
            CompanyFactory.create_batch(
                size=n_companies,
                created_by=adviser,
                modified_by=adviser,
            )
        )
        companies.extend(
            CompanyWithAreaFactory.create_batch(
                size=n_companies_with_area,
                created_by=adviser,
                modified_by=adviser,
            )
        )
        
        # Create subsidiaries
        for company in companies[:n_subsidiary_companies]:
            SubsidiaryFactory(
                created_by=adviser,
                modified_by=adviser,
                global_headquarters=company,
            )

        # Create archived and duplicate companies
        ArchivedCompanyFactory.create_batch(
            size=n_archived_companies,
            created_by=adviser,
            modified_by=adviser,
        )
        DuplicateCompanyFactory.create_batch(
            size=n_duplicate_companies,
            created_by=adviser,
            modified_by=adviser,
        )
        send_heartbeat_every_10_iterations(index)
    print(f'\nGenerated {number_of_companies} companies')  # noqa
