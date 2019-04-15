import uuid
from datetime import datetime

import pytest
from django.conf import settings
from django.core.management import call_command
from django.utils.timezone import utc
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import Country as CountryConstant
from datahub.dnb_match.management.commands.cleanse_companies_using_worldbase_match import (
    Command as CleanseCommand,
)
from datahub.dnb_match.test.factories import DnBMatchingResultFactory
from datahub.dnb_match.utils import (
    ARCHIVED_REASON_DISSOLVED,
    EmployeesIndicator,
    NATIONAL_ID_SYSTEM_CODE_UK,
    OutOfBusinessIndicator,
    TurnoverIndicator,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.test.factories import OrderFactory

pytestmark = pytest.mark.django_db


FROZEN_TIME = datetime(2019, 1, 1, 1, tzinfo=utc)
UNITED_KINGDOM_COUNTRY_UUID = uuid.UUID(CountryConstant.united_kingdom.value.id)
DATAHUB_FRONTEND_COMPANY_PREFIX = settings.DATAHUB_FRONTEND_URL_PREFIXES['company']


TEST_DATA = [
    # Cleansed
    {
        'company': {
            'id': uuid.UUID('00000000-0000-0000-0000-000000000001'),
            'duns_number': None,
        },
        'dnbmatchingresult_data': {
            'dnb_match': {
                'duns_number': '000000001',
            },
            'wb_record': {
                'DUNS Number': '000000001',
                'Business Name': 'WB Corp',
                'Secondary Name': 'Known as...',
                'Employees Total': '11',
                'Employees Total Indicator': EmployeesIndicator.ESTIMATED.value,
                'Employees Here': '0',
                'Employees Here Indicator': EmployeesIndicator.ESTIMATED.value,
                'Annual Sales in US dollars': '100',
                'Annual Sales Indicator': TurnoverIndicator.ESTIMATED.value,
                'Street Address': '1',
                'Street Address 2': 'Main Street',
                'City Name': 'London',
                'State/Province Name': 'Camden',
                'Country Code': '785',
                'Postal Code for Street Address': 'SW1A 1AA',
                'National Identification Number': '12345678',
                'National Identification System Code': str(NATIONAL_ID_SYSTEM_CODE_UK),
                'Out of Business indicator': OutOfBusinessIndicator.NOT_OUT_OF_BUSINESS.value,
            },
        },
        'expected_fields': {
            'duns_number': '000000001',
            'name': 'WB Corp',
            'trading_names': ['Known as...'],
            'company_number': '12345678',
            'number_of_employees': 11,
            'is_number_of_employees_estimated': True,
            'employee_range': None,
            'turnover': 100,
            'is_turnover_estimated': True,
            'turnover_range': None,
            'address_1': '1',
            'address_2': 'Main Street',
            'address_town': 'London',
            'address_county': 'Camden',
            'address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
            'address_postcode': 'SW1A 1AA',
            'registered_address_1': '1',
            'registered_address_2': 'Main Street',
            'registered_address_town': 'London',
            'registered_address_county': 'Camden',
            'registered_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
            'registered_address_postcode': 'SW1A 1AA',
            'trading_address_1': '1',
            'trading_address_2': 'Main Street',
            'trading_address_town': 'London',
            'trading_address_county': 'Camden',
            'trading_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
            'trading_address_postcode': 'SW1A 1AA',
        },
    },

    # raises KeyError as wb_record doesn't have all the needed data
    {
        'company': {
            'id': uuid.UUID('00000000-0000-0000-0000-000000000002'),
            'name': 'Dean-Gordon',
            'duns_number': None,
        },
        'dnbmatchingresult_data': {
            'dnb_match': {
                'duns_number': '000000002',
            },
            'wb_record': {
                'DUNS Number': '000000002',
            },
        },
        'expected_fields': {},
    },

    # Company.duns_number is set so the record should be ignored.
    {
        'company': {
            'id': uuid.UUID('00000000-0000-0000-0000-000000000003'),
            'duns_number': '000000003',
        },
        'dnbmatchingresult_data': {
            'dnb_match': {
                'duns_number': '200000000',
            },
            'wb_record': {
                'DUNS Number': '200000000',
            },
        },
        'expected_fields': {
            'duns_number': '000000003',
        },
    },

    # next 2 ignored as there are 2 dnbmatchingresults with the same duns_number
    # so the companies are duplicate - ignored as they can't be cleansed automatically.
    {
        'company': {
            'id': uuid.UUID('00000000-0000-0000-0000-000000000004'),
            'duns_number': None,
        },
        'dnbmatchingresult_data': {
            'dnb_match': {
                'duns_number': '000000004',
            },
            'wb_record': {
                'DUNS Number': '000000004',
            },
        },
        'expected_fields': {
            'duns_number': None,
        },
    },
    {
        'company': {
            'id': uuid.UUID('00000000-0000-0000-0000-000000000005'),
            'duns_number': None,
        },
        'dnbmatchingresult_data': {
            'dnb_match': {
                'duns_number': '000000004',
            },
            'wb_record': {
                'DUNS Number': '000000004',
            },
        },
        'expected_fields': {
            'duns_number': None,
        },
    },

    # Cleansed with minimal worldbase record / Data Hub company archived
    {
        'company': {
            'id': uuid.UUID('00000000-0000-0000-0000-000000000006'),
            'duns_number': None,
        },
        'dnbmatchingresult_data': {
            'dnb_match': {
                'duns_number': '000000006',
            },
            'wb_record': {
                'DUNS Number': '000000006',
                'Business Name': 'WB Corp 2',
                'Secondary Name': '',
                'Employees Total': '0',
                'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE.value,
                'Employees Here': '0',
                'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE.value,
                'Annual Sales in US dollars': '0',
                'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE.value,
                'Street Address': '',
                'Street Address 2': '',
                'City Name': '',
                'State/Province Name': '',
                'Country Code': '785',
                'Postal Code for Street Address': '',
                'National Identification Number': '',
                'National Identification System Code': '',
                'Out of Business indicator': OutOfBusinessIndicator.OUT_OF_BUSINESS.value,
            },
        },
        'expected_fields': {
            'duns_number': '000000006',
            'name': 'WB Corp 2',
            'trading_names': [],
            'company_number': '',
            'number_of_employees': None,
            'is_number_of_employees_estimated': None,
            'employee_range': None,
            'turnover': None,
            'is_turnover_estimated': None,
            'turnover_range': None,
            'address_1': '',
            'address_2': '',
            'address_town': '',
            'address_county': '',
            'address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
            'address_postcode': '',
            'registered_address_1': '',
            'registered_address_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
            'registered_address_postcode': '',
            'trading_address_1': '',
            'trading_address_2': '',
            'trading_address_town': '',
            'trading_address_county': '',
            'trading_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
            'trading_address_postcode': '',
            'archived': True,
            'archived_on': FROZEN_TIME,
            'archived_reason': ARCHIVED_REASON_DISSOLVED,
        },
    },

    # Should be ignored as a Data Hub company with 'duns_number == '000000007'
    # already exists in the database
    {
        'company': {
            'id': uuid.UUID('00000000-0000-0000-0000-000000000007'),
            'duns_number': None,
        },
        'dnbmatchingresult_data': {
            'dnb_match': {
                'duns_number': '000000007',
            },
            'wb_record': {
                'DUNS Number': '000000007',
                'Business Name': 'WB Corp 3',
                'Secondary Name': '',
                'Employees Total': '0',
                'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE.value,
                'Employees Here': '0',
                'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE.value,
                'Annual Sales in US dollars': '0',
                'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE.value,
                'Street Address': '',
                'Street Address 2': '',
                'City Name': '',
                'State/Province Name': '',
                'Country Code': '785',
                'Postal Code for Street Address': '',
                'National Identification Number': '',
                'National Identification System Code': '',
                'Out of Business indicator': OutOfBusinessIndicator.OUT_OF_BUSINESS.value,
            },
        },
        'expected_fields': {},
    },
]


@pytest.mark.parametrize('simulate', (False, True))
@freeze_time(FROZEN_TIME)
def test_run(caplog, monkeypatch, simulate):
    """
    Test that the matched Worldbase records are used to cleanse Data Hub companies.
    """
    # add ordering to command queryset so that we can trigger an error
    # with the last record being processed
    original_get_companies_queryset = CleanseCommand._get_companies_queryset
    monkeypatch.setattr(
        CleanseCommand,
        '_get_companies_queryset',
        lambda self: original_get_companies_queryset(self).order_by('id'),
    )

    caplog.set_level('INFO')

    # set up data
    for test_data_item in TEST_DATA:
        company = CompanyFactory(**test_data_item['company'])
        InvestmentProjectFactory(investor_company=company)
        InvestmentProjectFactory(intermediate_company=company)
        InvestmentProjectFactory(uk_company=company)
        OrderFactory(company=company)

        DnBMatchingResultFactory(company=company, data=test_data_item['dnbmatchingresult_data'])

    CompanyFactory(duns_number='000000007')

    call_command('cleanse_companies_using_worldbase_match', simulate=simulate)

    assert caplog.messages == [
        'Started',
        'Company WB Corp - OK',
        (
            'Company Dean-Gordon - 00000000-0000-0000-0000-000000000002 '
            'failed: KeyError(\'Business Name\')'
        ),
        'Company WB Corp 2 - OK',
        'Finished - succeeded: 2, failed: 1, archived: 1',
        (
            'The following companies were archived but have related objects '
            'so they might require futher offline work. Please check with your Product Manager:'
        ),
        (
            f'{DATAHUB_FRONTEND_COMPANY_PREFIX}/00000000-0000-0000-0000-000000000006: '
            'intermediate_investment_projects, investee_projects, investor_investment_projects, '
            'orders'
        ),
    ]

    # check database
    for test_data_item in TEST_DATA:
        company = Company.objects.get(id=test_data_item['company']['id'])

        if not simulate:
            actual_fields = {
                field_name: getattr(company, field_name)
                for field_name in test_data_item['expected_fields']
            }
            assert actual_fields == test_data_item['expected_fields']

            # check revisions: if duns_number didn't change, the record wasn't cleansed so
            # no revision was created
            versions = Version.objects.get_for_object(company)
            if company.duns_number == test_data_item['company']['duns_number']:
                assert versions.count() == 0
            else:
                assert versions.count() == 1
                assert versions[0].revision.get_comment() == 'Updated from Dun & Bradstreet data.'
        else:
            # check that company.duns_number didn't change
            assert company.duns_number == test_data_item['company']['duns_number']

            # check that no revision was created
            versions = Version.objects.get_for_object(company)
            assert versions.count() == 0


@pytest.mark.parametrize('simulate', (False, True))
def test_run_without_any_matches(caplog, simulate):
    """
    Test that if no matches are found in the database, the command reports zero results.
    """
    CompanyFactory.create_batch(5)

    caplog.set_level('INFO')

    call_command('cleanse_companies_using_worldbase_match', simulate=simulate)

    assert caplog.messages == [
        'Started',
        'Finished - succeeded: 0, failed: 0, archived: 0',
    ]
