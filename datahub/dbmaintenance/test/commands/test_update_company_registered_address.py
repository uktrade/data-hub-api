import pytest
from django.core.management import call_command

from datahub.company.models import Company
from datahub.company.test.factories import (
    CompaniesHouseCompanyFactory,
    CompanyFactory,
)


@pytest.fixture()
def company_company_house_data(db):
    """
    Create a CompaniesHouseCompany that has a company number that matches
    Company and one that doesn't.
    """
    CompanyFactory(company_number='1')
    CompaniesHouseCompanyFactory(company_number='1')
    CompanyFactory(company_number='2')
    CompaniesHouseCompanyFactory(company_number='3')


def _is_address_same(company1, company2):
    """
    Check if the given companies have same
    address.
    """
    fields = [
        'registered_address_town',
        'registered_address_town',
        'registered_address_1',
        'registered_address_2',
        'registered_address_county',
        'registered_address_country',
        'registered_address_postcode',
    ]
    field_matches = [
        getattr(company1, field) == getattr(company2, field)
        for field in fields
    ]
    return all(field_matches)


@pytest.mark.usefixtures('company_company_house_data')
def test_run():
    """."""
    call_command('update_company_registered_address')
    for company in Company.objects.all():
        ch_data = company.companies_house_data
        if ch_data is not None:
            assert _is_address_same(company, ch_data)
