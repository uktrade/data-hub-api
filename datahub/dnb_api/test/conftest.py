import datetime

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.company.test.factories import CompanyFactory
from datahub.dnb_api.constants import FEATURE_FLAG_DNB_COMPANY_SEARCH
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction.test.factories import CompanyInteractionFactory


@pytest.fixture
def dnb_company_search_feature_flag(db):
    """
    Creates the dnb company search feature flag.
    """
    yield FeatureFlagFactory(code=FEATURE_FLAG_DNB_COMPANY_SEARCH)


@pytest.fixture
def dnb_response_non_uk():
    """
    Fixture for a record as returned by the dnb-service.
    """
    return {
        'results': [
            {
                'duns_number': '157270606',
                'primary_name': 'Acme Corporation',
                'trading_names': [
                    'Acme',
                ],
                'registration_numbers': [
                    {
                        'registration_type': 'unmapped',
                        'original_registration_type': 6863,
                        'original_registration_number': '24-3733147',
                        'original_registration_description':
                            'Federal Taxpayer Identification Number (US)',
                    },
                ],
                'global_ultimate_duns_number': '157270606',
                'global_ultimate_primary_name': 'Acme Corporation',
                'domain': 'acme.com',
                'is_out_of_business': False,
                'address_line_1': '150 Madison Ave',
                'address_line_2': '',
                'address_town': 'New York',
                'address_county': '',
                'address_postcode': '10033-1062',
                'address_country': 'US',
                'annual_sales': 1000000.0,
                'annual_sales_currency': 'USD',
                'is_annual_sales_estimated': None,
                'employee_number': 100,
                'is_employees_number_estimated': False,
                'primary_industry_codes': [
                    {
                        'usSicV4': '2325',
                        'usSicV4Description': "Mfg men's/boy's trousers",
                    },
                ],
                'industry_codes': [
                    {
                        'code': '315220',
                        'description': 'Men’s and Boys’ Cut and Sew Apparel Manufacturing',
                        'typeDescription': 'North American Industry Classification System 2017',
                        'typeDnbCode': 30832,
                        'priority': 2,
                    },
                    {
                        'code': '315990',
                        'description': 'Apparel Accessories and Other Apparel Manufacturing',
                        'typeDescription': 'North American Industry Classification System 2017',
                        'typeDnbCode': 30832,
                        'priority': 4,
                    },
                ],
                'legal_status': 'corporation',
            },
        ],
    }


@pytest.fixture
def dnb_response_uk():
    """
    Returns a UK-based DNB company.
    """
    return {
        'results': [
            {
                'address_country': 'GB',
                'address_county': '',
                'address_line_1': 'Unit 10, Ockham Drive',
                'address_line_2': '',
                'address_postcode': 'UB6 0F2',
                'address_town': 'GREENFORD',
                'annual_sales': 50651895.0,
                'annual_sales_currency': 'USD',
                'domain': 'foo.com',
                'duns_number': '291332174',
                'employee_number': 260,
                'global_ultimate_duns_number': '291332174',
                'global_ultimate_primary_name': 'FOO BICYCLE LIMITED',
                'industry_codes': [
                    {
                        'code': '336991',
                        'description': 'Motorcycle, Bicycle, and Parts Manufacturing',
                        'priority': 1,
                        'typeDescription': 'North American Industry Classification System 2017',
                        'typeDnbCode': 30832,
                    },
                    {
                        'code': '1927',
                        'description': 'Motorcycle Manufacturing',
                        'priority': 1,
                        'typeDescription': 'D&B Hoovers Industry Code',
                        'typeDnbCode': 25838,
                    },
                ],
                'is_annual_sales_estimated': None,
                'is_employees_number_estimated': True,
                'is_out_of_business': False,
                'legal_status': 'corporation',
                'primary_industry_codes': [
                    {
                        'usSicV4': '3751',
                        'usSicV4Description': 'Mfg motorcycles/bicycles',
                    },
                ],
                'primary_name': 'FOO BICYCLE LIMITED',
                'registered_address_country': 'GB',
                'registered_address_county': '',
                'registered_address_line_1': 'C/O LONE VARY',
                'registered_address_line_2': '',
                'registered_address_postcode': 'UB6 0F2',
                'registered_address_town': 'GREENFORD',
                'registration_numbers': [
                    {
                        'registration_number': '01261539',
                        'registration_type': 'uk_companies_house_number',
                    },
                ],
                'trading_names': [],
            },
        ],
    }


@pytest.fixture
def dnb_company_search_datahub_companies():
    """
    Creates Data Hub companies for hydrating DNB search results with.
    """
    # Company with no interactions
    CompanyFactory(duns_number='1234567', id='6083b732-b07a-42d6-ada4-c8082293285b')
    # Company with two interactions
    company = CompanyFactory(duns_number='7654321', id='6083b732-b07a-42d6-ada4-c99999999999')

    interaction_date = datetime.datetime(year=2019, month=8, day=1, hour=16, minute=0, tzinfo=utc)
    with freeze_time(interaction_date):
        CompanyInteractionFactory(
            id='6083b732-b07a-42d6-ada4-222222222222',
            date=interaction_date,
            subject='Meeting with Joe Bloggs',
            company=company,
        )

    older_interaction_date = datetime.datetime(year=2018, month=8, day=1, tzinfo=utc)
    with freeze_time(older_interaction_date):
        CompanyInteractionFactory(
            id='6083b732-b07a-42d6-ada4-111111111111',
            date=older_interaction_date,
            subject='Meeting with John Smith',
            company=company,
        )
