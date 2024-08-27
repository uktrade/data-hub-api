import datetime

import pytest

from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import EYBLeadFactory


@pytest.fixture
def data_flow_api_client(hawk_api_client):
    """Hawk API client fixture configured to use credentials with the data_flow_api scope."""
    hawk_api_client.set_credentials(
        'data-flow-api-id',
        'data-flow-api-key',
    )
    yield hawk_api_client


@pytest.fixture
def eyb_lead_data():
    return {
        # EYB Triage data
        'triage_id': 96,
        'triage_hashed_uuid': 'b85dabe2a4c46828424d61ec99f496d91952f9e53733898ff5f0fee89f08b635',
        'triage_created': datetime.datetime(
            2023, 9, 21, 7, 53, 19, 534794, tzinfo=datetime.timezone.utc,
        ),
        'triage_modified': datetime.datetime(
            2023, 9, 27, 11, 32, 28, 853014, tzinfo=datetime.timezone.utc,
        ),
        'sector': 'FOOD_AND_DRINK',
        'sector_sub': 'PROCESSING_AND_PRESERVING_OF_MEAT',
        'intent': [
            'SET_UP_NEW_PREMISES',
            'SET_UP_A_NEW_DISTRIBUTION_CENTRE',
            'ONWARD_SALES_AND_EXPORTS_FROM_THE_UK',
        ],
        'intent_other': 'other intent',
        'location': 'NORTHERN_IRELAND',
        'location_city': 'ARMAGH_CITY',
        'location_none': False,
        'hiring': '51-100',
        'spend': '1000000-2000000',
        'spend_other': '1234565432',
        'is_high_value': True,

        # EYB User data
        'user_id': 90,
        'user_hashed_uuid': 'b85dabe2a4c46828424d61ec99f496d91952f9e53733898ff5f0fee89f08b635',
        'user_created': datetime.datetime(
            2023, 9, 21, 7, 53, 19, 472710, tzinfo=datetime.timezone.utc,
        ),
        'user_modified': datetime.datetime(
            2023, 9, 22, 8, 53, 19, 472723, tzinfo=datetime.timezone.utc,
        ),
        'company_name': 'Stu co',
        'company_location': 'FR',
        'full_name': 'John Doe',
        'role': 'Director',
        'email': 'foo@bar.com',
        'telephone_number': '447923454678',
        'agree_terms': True,
        'agree_info_email': False,
        'landing_timeframe': 'SIX_TO_TWELVE_MONTHS',
        'company_website': 'http://www.google.com',
    }


@pytest.fixture
def eyb_lead_db(eyb_lead_data):
    eyb_lead_factory = EYBLeadFactory(**eyb_lead_data)
    return EYBLead.objects.get(pk=eyb_lead_factory.pk)
