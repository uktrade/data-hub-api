import datetime

from datahub.investment_lead.models import EYBLead


def _to_iso(dateobject):
    if isinstance(dateobject, datetime.datetime):
        return dateobject.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return dateobject


def assert_datetimes(first, second):
    assert _to_iso(first) == _to_iso(second)


def verify_eyb_lead_data(instance: EYBLead, data: dict):
    """Method to verify the EYBLead data against the instance created."""
    # EYB Triage data
    assert instance.triage_id == data['triage_id']
    assert instance.triage_hashed_uuid == data['triage_hashed_uuid']
    assert_datetimes(instance.triage_created, data['triage_created'])
    assert_datetimes(instance.triage_modified, data['triage_modified'])
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
    assert_datetimes(instance.user_created, data['user_created'])
    assert_datetimes(instance.user_modified, data['user_modified'])
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
