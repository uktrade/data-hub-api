import pytest

from datahub.core import constants
from datahub.core.test_utils import create_test_user
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.metadata.models import (
    Country,
    Sector,
    UKRegion,
)

DATETIME_STRING = '2024-09-04T08:02:30.123456Z'


@pytest.fixture
def test_user_with_view_permissions():
    return create_test_user(permission_codenames=['view_eyblead'])


@pytest.fixture
def eyb_lead_post_data():
    return {
        # EYB triage fields
        'triage_hashed_uuid': 'f9daca9c9ad9736cac5da34c6c65f343ed3bf7aee68cb5bdcef33684ed25d662',
        'triage_created': DATETIME_STRING,
        'triage_modified': DATETIME_STRING,
        'sector': 'Mining vehicles, transport and equipment',
        'intent': [
            EYBLead.IntentChoices.RESEARCH_DEVELOP_AND_COLLABORATE.value,
            EYBLead.IntentChoices.SET_UP_A_NEW_DISTRIBUTION_CENTRE.value,
        ],
        'intent_other': '',
        'location': constants.UKRegion.wales.value.name,
        'location_city': 'Cardiff',
        'location_none': False,
        'hiring': EYBLead.HiringChoices.ONE_TO_FIVE.value,
        'spend': EYBLead.SpendChoices.FIVE_HUNDRED_THOUSAND_TO_ONE_MILLION.value,
        'spend_other': '',
        'is_high_value': False,

        # EYB user fields
        'user_hashed_uuid': 'f9daca9c9ad9736cac5da34c6c65f343ed3bf7aee68cb5bdcef33684ed25d662',
        'user_created': DATETIME_STRING,
        'user_modified': DATETIME_STRING,
        'company_name': 'Noble, Scott and Jackson',
        'duns_number': '004353373',
        'address_1': '4288 Rebecca Common Apt. 204',
        'address_2': 'Suite 707',
        'address_town': 'Port Robertville',
        'address_country': 'CA',
        'address_postcode': '87107',
        'company_website': 'http://www.stevens.org/',
        'full_name': 'James Swanson MD',
        'role': 'Manufacturing systems engineer',
        'email': 'whiteclifford@example.net',
        'telephone_number': '001-263-022-2444',
        'agree_terms': False,
        'agree_info_email': False,
        'landing_timeframe': EYBLead.LandingTimeframeChoices.UNDER_SIX_MONTHS.value,

        # EYB marketing fields
        'utm_name': 'utm-name',
        'utm_source': 'source',
        'utm_medium': 'medium',
        'utm_content': 'content',
    }


@pytest.fixture
def eyb_lead_factory_data(eyb_lead_post_data):
    data = eyb_lead_post_data.copy()
    mining_sector = Sector.objects.get(
        pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
    )
    wales_region = UKRegion.objects.get(
        pk=constants.UKRegion.wales.value.id,
    )
    canada_country = Country.objects.get(
        pk=constants.Country.canada.value.id,
    )
    data.update({
        'sector': mining_sector,
        'location': wales_region,
        'address_country': canada_country,
    })
    return data


@pytest.fixture
def eyb_lead_instance_from_db(eyb_lead_factory_data):
    eyb_lead_factory = EYBLeadFactory(**eyb_lead_factory_data)
    return EYBLead.objects.get(pk=eyb_lead_factory.pk)
