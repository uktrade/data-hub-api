import datetime

from datahub.investment_lead.models import EYBLead


def _to_iso(dateobject):
    if isinstance(dateobject, datetime.datetime):
        return dateobject.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return dateobject


def assert_datetimes(first, second):
    assert _to_iso(first) == _to_iso(second)


def verify_eyb_lead_data(instance: EYBLead, data: dict, is_factory_data: bool = False):
    """Method to verify the EYBLead data against the instance created.

    Use:
    - `is_factory_data=True` if passing in factory data which contains actual model
    instances for related fields
    - `is_factory_data=False` if passing in POST data that contains strings for
    these fields.

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
    assert data['sector'] == instance.sector \
        if is_factory_data else instance.sector.segment
    assert instance.sector_sub == data['sector_sub']
    assert instance.intent == data['intent']
    assert instance.intent_other == data['intent_other']
    assert data['location'] == instance.location \
        if is_factory_data else instance.location.name
    assert instance.location_city == data['location_city']
    assert instance.location_none == data['location_none']
    assert instance.hiring == data['hiring']
    assert instance.spend == data['spend']
    assert instance.spend_other == data['spend_other']
    assert instance.is_high_value == data['is_high_value']

    # EYB user fields
    assert instance.user_hashed_uuid == data['user_hashed_uuid']
    assert_datetimes(instance.user_created, data['user_created'])
    assert_datetimes(instance.user_modified, data['user_modified'])
    assert instance.company_name == data['company_name']
    assert data['company_location'] == instance.company_location \
        if is_factory_data else instance.company_location.iso_alpha2_code
    assert instance.full_name == data['full_name']
    assert instance.role == data['role']
    assert instance.email == data['email']
    assert instance.telephone_number == data['telephone_number']
    assert instance.agree_terms == data['agree_terms']
    assert instance.agree_info_email == data['agree_info_email']
    assert instance.landing_timeframe == data['landing_timeframe']

    # Company fields
    assert instance.duns_number == data['duns_number']
    assert instance.address_1 == data['address_1']
    assert instance.address_2 == data['address_2']
    assert instance.address_town == data['address_town']
    assert instance.address_county == data['address_county']
    assert data['address_area'] == instance.address_area \
        if is_factory_data else instance.address_area.name
    assert data['address_country'] == instance.address_country \
        if is_factory_data else instance.address_country.iso_alpha2_code
    assert instance.address_postcode == data['address_postcode']
