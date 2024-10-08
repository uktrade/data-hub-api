import datetime
from typing import Literal

from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.investment_lead.models import EYBLead


def _to_iso(dateobject):
    if isinstance(dateobject, datetime.datetime):
        return dateobject.astimezone().strftime('%Y-%m-%dT%H:%M:%SZ')
    return dateobject


def assert_datetimes(first, second):
    assert _to_iso(first) == _to_iso(second)


def verify_eyb_triage_data(
    instance: EYBLead, data: dict, data_type: Literal['json', 'factory', 'nested'],
):
    """Method to verify the EYB triage data against the created EYBLead instance.

    Use:
    - `data_type='json'` if passing in JSON data which contains string names
    for related fields
    - `data_type='factory'` if passing in factory (or validated serializer) data that
    contains model instances for these fields
    - `data_type='nested'` if passing in serialized data (from the RetrieveEYBLeadSerializer)
    that contains nested objects for these fields, with the id and name attributes.

    Related fields are:
    - Sector
    - Location
    """
    assert instance.triage_hashed_uuid == data['triage_hashed_uuid']
    assert_datetimes(instance.triage_created, data['triage_created'])
    assert_datetimes(instance.triage_modified, data['triage_modified'])
    assert instance.intent_other == data['intent_other']
    assert instance.location_city == data['location_city']
    assert instance.location_none == data['location_none']
    assert instance.spend_other == data['spend_other']
    assert instance.is_high_value == data['is_high_value']

    # Choice fields
    if data_type == 'nested':
        assert [
            EYBLead.IntentChoices(intent_choice).label
            for intent_choice in instance.intent
        ] == data['intent']
        assert EYBLead.HiringChoices(instance.hiring).label == data['hiring']
        assert EYBLead.SpendChoices(instance.spend).label == data['spend']
    else:
        assert instance.intent == data['intent']
        assert instance.hiring == data['hiring']
        assert instance.spend == data['spend']

    # Related fields
    if data_type == 'json':
        assert instance.sector.segment == data['sector']
        assert instance.location.name == data['location']
    elif data_type == 'factory':
        assert instance.sector == data['sector']
        assert instance.location == data['location']
    elif data_type == 'nested':
        assert str(instance.sector.id) == data['sector']['id']
        assert str(instance.location.id) == data['location']['id']
    else:
        raise ValueError(f'Invalid value "{data_type}" for argument data_type')


def verify_eyb_user_data(
    instance: EYBLead, data: dict, data_type: Literal['json', 'factory', 'nested'],
):
    """Method to verify the EYB user data against the created EYBLead instance.

    Use:
    - `data_type='json'` if passing in JSON data which contains string names
    for related fields
    - `data_type='factory'` if passing in factory (or validated serializer) data that
    contains model instances for these fields
    - `data_type='nested'` if passing in serialized data (from the RetrieveEYBLeadSerializer)
    that contains nested objects for these fields, with the id and name attributes.

    Related fields are:
    - Address country
    """
    assert instance.user_hashed_uuid == data['user_hashed_uuid']
    assert_datetimes(instance.user_created, data['user_created'])
    assert_datetimes(instance.user_modified, data['user_modified'])
    assert instance.company_name == data['company_name']
    assert instance.duns_number == data['duns_number']
    assert instance.full_name == data['full_name']
    assert instance.role == data['role']
    assert instance.email == data['email']
    assert instance.telephone_number == data['telephone_number']
    assert instance.agree_terms == data['agree_terms']
    assert instance.agree_info_email == data['agree_info_email']

    # Address fields
    if data_type != 'nested':
        assert instance.address_1 == data['address_1']
        assert instance.address_2 == data['address_2']
        assert instance.address_town == data['address_town']
        assert instance.address_postcode == data['address_postcode']
    else:
        assert instance.address_1 == data['address']['line_1']
        assert instance.address_2 == data['address']['line_2']
        assert instance.address_town == data['address']['town']
        assert instance.address_postcode == data['address']['postcode']

    # Choice fields
    if data_type == 'nested':
        assert EYBLead.LandingTimeframeChoices(instance.landing_timeframe).label \
            == data['landing_timeframe']
    else:
        assert instance.landing_timeframe == data['landing_timeframe']

    # Related fields
    if data_type == 'json':
        assert instance.address_country.iso_alpha2_code == data['address_country']
    elif data_type == 'factory':
        assert instance.address_country == data['address_country']
    elif data_type == 'nested':
        assert str(instance.address_country.id) == data['address']['country']['id']
        assert str(instance.company.id) == data['company']['id']
    else:
        raise ValueError(f'Invalid value "{data_type}" for argument data_type')


def verify_eyb_marketing_data(instance: EYBLead, data: dict):
    """Method to verify the EYB marketing data against the created EYBLead instance."""
    assert instance.utm_name == data['utm_name']
    assert instance.utm_source == data['utm_source']
    assert instance.utm_medium == data['utm_medium']
    assert instance.utm_content == data['utm_content']


def verify_eyb_lead_data(
    instance: EYBLead, data: dict, data_type: Literal['json', 'factory', 'nested'],
):
    """Method to verify an EYB lead instance against all data components that made it.

    Use:
    - `data_type='json'` if passing in JSON data which contains string names
    for related fields
    - `data_type='factory'` if passing in factory (or validated serializer) data that
    contains model instances for these fields
    - `data_type='nested'` if passing in serialized data (from the RetrieveEYBLeadSerializer)
    that contains nested objects for these fields, with the id and name attributes.

    Related fields are:
    - Sector
    - Location
    - Address country
    """
    verify_eyb_triage_data(instance, data, data_type)
    verify_eyb_user_data(instance, data, data_type)
    verify_eyb_marketing_data(instance, data)


def assert_eyb_lead_matches_company(company: Company, eyb_lead: EYBLead):
    assert eyb_lead.duns_number == company.duns_number
    assert eyb_lead.company_name == company.name
    assert eyb_lead.sector == company.sector
    assert eyb_lead.address_1 == company.address_1
    assert eyb_lead.address_2 == company.address_2
    assert eyb_lead.address_town == company.address_town
    assert eyb_lead.address_country == company.address_country
    assert eyb_lead.address_postcode == company.address_postcode
    assert eyb_lead.company_website == company.website

    assert eyb_lead.company == company


def assert_eyb_lead_matches_contact(contact: Contact, eyb_lead: EYBLead):
    assert eyb_lead.company == contact.company
    assert eyb_lead.email == contact.email
    assert eyb_lead.telephone_number == contact.full_telephone_number
    assert eyb_lead.role == contact.job_title
    assert eyb_lead.full_name == contact.first_name
    assert eyb_lead.full_name == contact.last_name
    assert contact.address_same_as_company
    assert contact.primary
