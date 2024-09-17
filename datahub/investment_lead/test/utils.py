import datetime
from typing import Literal

from datahub.company.models.company import Company
from datahub.investment_lead.models import EYBLead


def _to_iso(dateobject):
    if isinstance(dateobject, datetime.datetime):
        return dateobject.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return dateobject


def assert_datetimes(first, second):
    assert _to_iso(first) == _to_iso(second)


def verify_eyb_lead_data(
    instance: EYBLead, data: dict, data_type: Literal['post', 'factory', 'nested'],
):
    """Method to verify the EYBLead data against the passed instance.

    Use:
    - `data_type='post'` if passing in POST data which contains string names
    for related fields
    - `data_type='factory'` if passing in factory (or validated serializer) data that
    contains model instances for these fields
    - `data_type='nested'` if passing in serialized data (from the RetrieveEYBLeadSerializer)
    that contains nested objects for these fields, with the id and name attributes.

    Related fields are:
    - Sector
    - Location
    - Company location
    - Address area
    - Address country
    """
    # EYB triage fields
    assert instance.triage_hashed_uuid == data['triage_hashed_uuid']
    assert_datetimes(instance.triage_created, data['triage_created'])
    assert_datetimes(instance.triage_modified, data['triage_modified'])
    assert instance.sector_sub == data['sector_sub']
    assert instance.intent_other == data['intent_other']
    assert instance.location_city == data['location_city']
    assert instance.location_none == data['location_none']
    assert instance.spend_other == data['spend_other']
    assert instance.is_high_value == data['is_high_value']

    # EYB user fields
    assert instance.user_hashed_uuid == data['user_hashed_uuid']
    assert_datetimes(instance.user_created, data['user_created'])
    assert_datetimes(instance.user_modified, data['user_modified'])
    assert instance.company_name == data['company_name']
    assert instance.full_name == data['full_name']
    assert instance.role == data['role']
    assert instance.email == data['email']
    assert instance.telephone_number == data['telephone_number']
    assert instance.agree_terms == data['agree_terms']
    assert instance.agree_info_email == data['agree_info_email']

    # Company fields
    assert instance.duns_number == data['duns_number']

    # Address fields
    if data_type != 'nested':
        assert instance.address_1 == data['address_1']
        assert instance.address_2 == data['address_2']
        assert instance.address_town == data['address_town']
        assert instance.address_county == data['address_county']
        assert instance.address_postcode == data['address_postcode']
    else:
        assert instance.address_1 == data['address']['line_1']
        assert instance.address_2 == data['address']['line_2']
        assert instance.address_town == data['address']['town']
        assert instance.address_county == data['address']['county']
        assert instance.address_postcode == data['address']['postcode']

    # Choice fields
    if data_type == 'nested':
        assert [
            EYBLead.IntentChoices(intent_choice).label
            for intent_choice in instance.intent
        ] == data['intent']
        assert EYBLead.HiringChoices(instance.hiring).label == data['hiring']
        assert EYBLead.SpendChoices(instance.spend).label == data['spend']
        assert EYBLead.LandingTimeframeChoices(instance.landing_timeframe).label \
            == data['landing_timeframe']
    else:
        assert instance.intent == data['intent']
        assert instance.hiring == data['hiring']
        assert instance.spend == data['spend']
        assert instance.landing_timeframe == data['landing_timeframe']

    # Related fields
    if data_type == 'post':
        assert instance.sector.segment == data['sector']
        assert instance.location.name == data['location']
        assert instance.company_location.iso_alpha2_code == data['company_location']
        assert instance.address_area.name == data['address_area']
        assert instance.address_country.iso_alpha2_code == data['address_country']
    elif data_type == 'factory':
        assert instance.sector == data['sector']
        assert instance.location == data['location']
        assert instance.company_location == data['company_location']
        assert instance.address_area == data['address_area']
        assert instance.address_country == data['address_country']
    elif data_type == 'nested':
        assert str(instance.sector.id) == data['sector']['id']
        assert str(instance.location.id) == data['location']['id']
        assert str(instance.company_location.id) == data['company_location']['id']
        assert str(instance.address_area.id) == data['address']['area']['id']
        assert str(instance.address_country.id) == data['address']['country']['id']
        assert str(instance.company.id) == data['company']['id']
    else:
        raise ValueError(f'Invalid value "{data_type}" for argument data_type')


def assert_company_matches_eyb_lead(eyb_lead: EYBLead, company: Company):
    """Method to verify the EYBLead data against the passed instance.

    Use:
    - `data_type='post'` if passing in POST data which contains string names
    for related fields
    - `data_type='factory'` if passing in factory (or validated serializer) data that
    contains model instances for these fields
    - `data_type='nested'` if passing in serialized data (from the RetrieveEYBLeadSerializer)
    that contains nested objects for these fields, with the id and name attributes.

    Related fields are:
    - Sector
    - Location
    - Company location
    - Address area
    - Address country
    """
    # # EYB triage fields
    # assert eyb_lead.triage_hashed_uuid == data['triage_hashed_uuid']
    # assert_datetimes(eyb_lead.triage_created, data['triage_created'])
    # assert_datetimes(eyb_lead.triage_modified, data['triage_modified'])
    # assert eyb_lead.sector_sub == data['sector_sub']
    # assert eyb_lead.intent == data['intent']
    # assert eyb_lead.intent_other == data['intent_other']
    # assert eyb_lead.location_city == data['location_city']
    # assert eyb_lead.location_none == data['location_none']
    # assert eyb_lead.hiring == data['hiring']
    # assert eyb_lead.spend == data['spend']
    # assert eyb_lead.spend_other == data['spend_other']
    # assert eyb_lead.is_high_value == data['is_high_value']

    # # EYB user fields
    # assert eyb_lead.user_hashed_uuid == data['user_hashed_uuid']
    # assert_datetimes(eyb_lead.user_created, data['user_created'])
    # assert_datetimes(eyb_lead.user_modified, data['user_modified'])
    # assert eyb_lead.company_name == data['company_name']
    # assert eyb_lead.full_name == data['full_name']
    # assert eyb_lead.role == data['role']
    # assert eyb_lead.email == data['email']
    # assert eyb_lead.telephone_number == data['telephone_number']
    # assert eyb_lead.agree_terms == data['agree_terms']
    # assert eyb_lead.agree_info_email == data['agree_info_email']
    # assert eyb_lead.landing_timeframe == data['landing_timeframe']

    # # Company fields
    # assert eyb_lead.duns_number == data['duns_number']

    # # Address fields
    # if data_type != 'nested':
    #     assert eyb_lead.address_1 == data['address_1']
    #     assert eyb_lead.address_2 == data['address_2']
    #     assert eyb_lead.address_town == data['address_town']
    #     assert eyb_lead.address_county == data['address_county']
    #     assert eyb_lead.address_postcode == data['address_postcode']
    # else:
    #     assert eyb_lead.address_1 == data['address']['line_1']
    #     assert eyb_lead.address_2 == data['address']['line_2']
    #     assert eyb_lead.address_town == data['address']['town']
    #     assert eyb_lead.address_county == data['address']['county']
    #     assert eyb_lead.address_postcode == data['address']['postcode']

    # # Related fields
    # if data_type == 'post':
    #     assert eyb_lead.sector.segment == data['sector']
    #     assert eyb_lead.location.name == data['location']
    #     assert eyb_lead.company_location.iso_alpha2_code == data['company_location']
    #     assert eyb_lead.address_area.name == data['address_area']
    #     assert eyb_lead.address_country.iso_alpha2_code == data['address_country']
    # elif data_type == 'factory':
    #     assert eyb_lead.sector == data['sector']
    #     assert eyb_lead.location == data['location']
    #     assert eyb_lead.company_location == data['company_location']
    #     assert eyb_lead.address_area == data['address_area']
    #     assert eyb_lead.address_country == data['address_country']
    # elif data_type == 'nested':
    #     assert str(eyb_lead.sector.id) == data['sector']['id']
    #     assert str(eyb_lead.location.id) == data['location']['id']
    #     assert str(eyb_lead.company_location.id) == data['company_location']['id']
    #     assert str(eyb_lead.address_area.id) == data['address']['area']['id']
    #     assert str(eyb_lead.address_country.id) == data['address']['country']['id']
    # else:
    #     raise ValueError(f'Invalid value "{data_type}" for argument data_type')
