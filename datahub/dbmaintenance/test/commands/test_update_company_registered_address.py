from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import (
    CompaniesHouseCompanyFactory,
    CompanyFactory,
)
from datahub.core.constants import Country
from datahub.dbmaintenance.management.commands.update_company_registered_address import (
    copy_registered_address,
)


@pytest.fixture()
def company(db):
    """
    Create a Company, CompaniesHouseCompany pair with the same address.
    """
    address = {
        'registered_address_1': '12',
        'registered_address_2': 'Foo St.',
        'registered_address_town': 'London',
        'registered_address_county': 'Westminster',
        'registered_address_country_id': Country.united_kingdom.value.id,
        'registered_address_postcode': 'SW1 T2E',
    }
    company = CompanyFactory(company_number='1', **address)
    CompaniesHouseCompanyFactory(company_number='1', **address)

    return company


def is_address_same(company_number):
    """
    Check if address is the same for the Company & CompaniesHouseCompany
    with the given company_number.
    """
    fields = {
        'registered_address_1',
        'registered_address_2',
        'registered_address_town',
        'registered_address_county',
        'registered_address_country',
        'registered_address_postcode',
    }

    company = Company.objects.get(company_number=company_number)
    ch_company = company.companies_house_data

    field_matches = [
        getattr(company, field) == getattr(ch_company, field)
        for field in fields
    ]

    return all(field_matches)


@pytest.mark.parametrize(
    'field, value',
    (
        ('registered_address_1', '10'),
        ('registered_address_2', 'Bar St.'),
        ('registered_address_town', 'Brighton'),
        ('registered_address_county', 'Surrey'),
        ('registered_address_country_id', Country.italy.value.id),
        ('registered_address_postcode', 'TW3 2YT'),
    ),
)
def test_different_address(field, value, company):
    """
    The command should copy the registered_address from CompaniesHouseCompany
    to Company and this should create a revision.
    """
    setattr(company, field, value)
    company.save()

    call_command('update_company_registered_address')

    assert is_address_same(company.company_number)

    versions = Version.objects.get_for_object(company)
    assert versions.count() == 1


def test_same_address(company):
    """
    When the address is same, we do not create a new revision.
    """
    call_command('update_company_registered_address')

    versions = Version.objects.get_for_object(company)
    assert versions.count() == 0


def test_no_ch_company(company):
    """
    When there is no matching CompaniesHouseCompany for a
    Company, we reset the address to blank and create revision.
    """
    company.company_number = 'NOT 1'
    company.save()
    call_command('update_company_registered_address')

    company.refresh_from_db()
    assert company.registered_address_1 == ''
    assert company.registered_address_2 == ''
    assert company.registered_address_town == ''
    assert company.registered_address_county == ''
    assert company.registered_address_country is None
    assert company.registered_address_postcode == ''

    versions = Version.objects.get_for_object(company)
    assert versions.count() == 1


def test_no_ch_company_address_blank(company):
    """
    When there is no matching CompaniesHouseCompany for a
    Company and the address is already blank, we do not
    create a revision.
    """
    company.company_number = 'NOT 1'
    company.registered_address_1 = ''
    company.registered_address_2 = ''
    company.registered_address_town = ''
    company.registered_address_county = ''
    company.registered_address_country = None
    company.registered_address_postcode = ''
    company.save()

    call_command('update_company_registered_address')

    versions = Version.objects.get_for_object(company)
    assert versions.count() == 0


def test_simulate(company):
    """
    When the command is run in simulate mode, we do not save
    the changes or create a revision.
    """
    company.registered_address_postcode = 'TW3 2TY'
    company.save()
    call_command('update_company_registered_address', simulate=True)

    assert not is_address_same(company.company_number)

    versions = Version.objects.get_for_object(company)
    assert versions.count() == 0


@pytest.mark.usefixtures('company')
@pytest.mark.parametrize('simulate', [True, False])
def test_logs(simulate, caplog):
    """
    The normal as well as simulated run of the command should produce logs
    when there are no exceptions.
    """
    with caplog.at_level('INFO'):
        call_command('update_company_registered_address', simulate=simulate)
        assert caplog.records[0].message == 'Started'
        assert caplog.records[-1].message == 'Finished - succeeded: 1, failed: 0'


@pytest.mark.usefixtures('company')
@patch(
    'datahub.dbmaintenance.management.commands'
    '.update_company_registered_address.Command'
    '._process_company',
    side_effect=Exception('Testing'),
)
@pytest.mark.parametrize('simulate', [True, False])
def test_logs_fail(_, simulate, caplog):
    """
    The normal as well as simulated run of the command should produce logs
    when it encounters exceptions.
    """
    with caplog.at_level('INFO'):
        call_command('update_company_registered_address', simulate=simulate)
        assert caplog.records[-1].message == 'Finished - succeeded: 0, failed: 1'


@pytest.mark.parametrize(
    'field, value',
    (
        ('registered_address_1', '10'),
        ('registered_address_2', 'Bar St.'),
        ('registered_address_town', 'Brighton'),
        ('registered_address_county', 'Surrey'),
        ('registered_address_country_id', Country.italy.value.id),
        ('registered_address_postcode', 'TW3 2YT'),
    ),
)
def test_copy_registered_address_different(field, value, company):
    """
    copy_registered_address should return True if any single field
    of the registered_address for the destination and source companies
    are different.
    """
    setattr(company, field, value)
    company.save()
    ch_company = company.companies_house_data
    assert copy_registered_address(company, ch_company)
    company.save()
    assert is_address_same(company.company_number)


def test_copy_registered_address_same(company):
    """
    copy_registered_address should return False if all registered_address
    fields are the same.
    """
    ch_company = company.companies_house_data
    assert not copy_registered_address(company, ch_company)


def test_process_company_fail(company, caplog):
    """
    Test that failure in processing a company doesn't mean we do not
    process subsequent companies.
    """
    # Change one of the fields of company
    company.registered_address_postcode = 'TW3 2TY'
    company.save()

    # Set up another company
    company_fail = CompanyFactory(
        company_number='2',
        registered_address_1='Fail St.',
    )
    CompaniesHouseCompanyFactory(
        company_number='2',
        registered_address_1='CH Fail St.',
    )

    # Set the new company to raise an Exception
    def companies_house_data_fail():
        raise Exception('Test')

    company_fail.companies_house_data = companies_house_data_fail

    # Set a mock queryset that includes the company_fail object
    mock_companies_queryset = Mock()
    mock_companies_queryset.iterator.return_value = (
        company_fail, company,
    )

    with patch(
        'datahub.dbmaintenance.management.commands'
        '.update_company_registered_address.Command'
        '._get_companies_queryset',
        return_value=mock_companies_queryset,
    ):
        with caplog.at_level('INFO'):
            call_command('update_company_registered_address')
            assert caplog.records[-1].message == 'Finished - succeeded: 1, failed: 1'

        # Failing company was not updated
        assert not is_address_same(company_fail.company_number)
        # Normal company is updated
        assert is_address_same(company.company_number)
