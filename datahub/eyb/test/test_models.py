import datetime
import factory
import pytest

from datahub.eyb.models import EYBLead
from datahub.eyb.test.factories import EYBLeadFactory


@pytest.fixture
def eyb_lead_data():
    return {
        # EYB Triage data
        'triage_id': 96,
        'triage_hashed_uuid': 'b85dabe2a4c46828424d61ec99f496d91952f9e53733898ff5f0fee89f08b635',
        'triage_created': datetime.datetime(2023, 9, 21, 7, 53, 19, 534794, tzinfo=datetime.timezone.utc),
        'triage_modified': datetime.datetime(2023, 9, 27, 11, 32, 28, 853014, tzinfo=datetime.timezone.utc),
        'sector': 'FOOD_AND_DRINK',
        'sector_sub': 'PROCESSING_AND_PRESERVING_OF_MEAT',
        'intent': [
            'SET_UP_NEW_PREMISES',
            'SET_UP_A_NEW_DISTRIBUTION_CENTRE',
            'ONWARD_SALES_AND_EXPORTS_FROM_THE_UK',
        ],
        'intent_other': '',
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
        'user_created': datetime.datetime(2023, 9, 21, 7, 53, 19, 472710, tzinfo=datetime.timezone.utc),
        'user_modified': datetime.datetime(2023, 9, 22, 8, 53, 19, 472723, tzinfo=datetime.timezone.utc),
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


def verify_eyb_lead_data(instance: EYBLead, data: dict):
    """Method to verify the EYBLead data against the instance created."""
    # EYB Triage data
    assert instance.triage_id == data['triage_id']
    assert instance.triage_hashed_uuid == data['triage_hashed_uuid']
    assert instance.triage_created == data['triage_created']
    assert instance.triage_modified == data['triage_modified']
    assert instance.sector == data['sector']
    assert instance.sector_sub == data['sector_sub']
    assert instance.intent == data['intent']
    assert instance.intent_other == data['intent_other']
    assert instance.location == data['location']
    assert instance.location_city == data['location_city']
    assert instance.location_none == data['location_none']
    assert instance.hiring == data['hiring']
    assert instance.spend == data['spend']
    assert instance.spend_other == data['spend_other']
    assert instance.is_high_value == data['is_high_value']

    # EYB User data
    assert instance.user_id == data['user_id']
    assert instance.user_hashed_uuid == data['user_hashed_uuid']
    assert instance.user_created == data['user_created']
    assert instance.user_modified == data['user_modified']
    assert instance.company_name == data['company_name']
    assert instance.company_location == data['company_location']
    assert instance.full_name == data['full_name']
    assert instance.role == data['role']
    assert instance.email == data['email']
    assert instance.telephone_number == data['telephone_number']
    assert instance.agree_terms == data['agree_terms']
    assert instance.agree_info_email == data['agree_info_email']
    assert instance.landing_timeframe == data['landing_timeframe']
    assert instance.company_website == data['company_website']


@pytest.mark.django_db
class TestEYBLead:
    """Tests EYB Lead model"""

    def test_db_instance_matches_factory_instance(self, eyb_lead_data):
        eyb_lead_factory = EYBLeadFactory(**eyb_lead_data)
        assert EYBLead.objects.all().exists()
        eyb_lead_db = EYBLead.objects.all().first()
        verify_eyb_lead_data(eyb_lead_db, eyb_lead_data)
