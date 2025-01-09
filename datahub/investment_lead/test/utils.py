from datetime import datetime, timezone

from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.core.utils import format_currency_range_string
from datahub.investment_lead.models import EYBLead
from datahub.metadata.models import Sector


def assert_datetimes(
    first_dt: datetime | str,
    second_dt: datetime | str,
    dt_format: str = '%Y-%m-%dT%H:%M:%S.%fZ',
):
    """Asserts that two datetime inputs are the same.

    In some cases, when asserting from model instances, the datetime fields
    don't include microseconds and need different formatting.
    """
    dt_format_without_microseconds = '%Y-%m-%dT%H:%M:%SZ'
    # Convert strings to datetime objects if necessary
    if isinstance(first_dt, str):
        try:
            first_dt = datetime.strptime(first_dt, dt_format)
        except ValueError:
            first_dt = datetime.strptime(first_dt, dt_format_without_microseconds)
    if isinstance(second_dt, str):
        try:
            second_dt = datetime.strptime(second_dt, dt_format)
        except ValueError:
            second_dt = datetime.strptime(second_dt, dt_format_without_microseconds)

    # Add timezone information if necessary
    if first_dt.tzinfo is None:
        first_dt = first_dt.replace(tzinfo=timezone.utc)
    if second_dt.tzinfo is None:
        second_dt = second_dt.replace(tzinfo=timezone.utc)

    assert first_dt == second_dt, f'the datetimes are not the same. {first_dt} != {second_dt}'


def assert_ingested_eyb_triage_data(instance: EYBLead, data: dict):
    """Method to verify the ingested EYB triage data against the created EYBLead instance.

    Notably, the ingested data has:
    - camelCase field names
    - strings for related fields.
    """
    assert instance.triage_hashed_uuid == data.get('hashedUuid')
    assert_datetimes(instance.triage_created, data.get('created'))
    assert_datetimes(instance.triage_modified, data.get('modified'))

    level_zero_segment, level_one_segment, level_two_segment = \
        Sector.get_segments_from_sector_instance(instance.sector)
    assert level_zero_segment == data.get('sector')
    assert level_one_segment == data.get('sectorSub', None)
    assert level_two_segment == data.get('sectorSubSub', None)

    assert instance.intent == data.get('intent', None)
    assert instance.intent_other == data.get('intentOther', None)
    if instance.proposed_investment_region is not None:
        assert instance.proposed_investment_region.name == data.get('location')
    else:
        assert instance.proposed_investment_region == data.get('location')
    assert instance.proposed_investment_city == data.get('locationCity', None)
    assert instance.proposed_investment_location_none == data.get('locationNone', None)
    assert instance.hiring == data.get('hiring', None)
    assert instance.spend == data.get('spend', None)
    assert instance.spend_other == data.get('spendOther', None)
    assert instance.is_high_value == data.get('isHighValue', None)


def assert_ingested_eyb_user_data(instance: EYBLead, data: dict):
    """Method to verify the ingested EYB user data against the created EYBLead instance.

    Notably, the ingested data has:
    - camelCase field names
    - strings for related fields.
    """
    assert instance.user_hashed_uuid == data.get('hashedUuid')
    assert_datetimes(instance.user_created, data.get('created'))
    assert_datetimes(instance.user_modified, data.get('modified'))
    assert instance.company_name == data.get('companyName')
    assert instance.duns_number == data.get('dunsNumber', None)
    assert instance.address_1 == data.get('addressLine1')
    assert instance.address_2 == data.get('addressLine2', None)
    assert instance.address_town == data.get('town')
    assert instance.address_county == data.get('county', None)
    assert instance.address_country.iso_alpha2_code == data.get('companyLocation')
    assert instance.address_postcode == data.get('postcode', None)
    assert instance.company_website == data.get('companyWebsite', None)
    assert instance.full_name == data.get('fullName')
    assert instance.role == data.get('role', None)
    assert instance.email == data.get('email')
    assert instance.telephone_number == data.get('telephoneNumber', None)
    assert instance.agree_terms == data.get('agreeTerms', None)
    assert instance.agree_info_email == data.get('agreeInfoEmail', None)
    assert instance.landing_timeframe == data.get('landingTimeframe', None)


def assert_ingested_eyb_marketing_data(instance: EYBLead, data: dict):
    """Method to verify the ingested EYB marketing data against the created EYBLead instance."""
    assert instance.utm_name == data.get('name')
    assert instance.utm_medium == data.get('medium')
    assert instance.utm_source == data.get('source')
    assert instance.utm_content == data.get('content')
    assert instance.marketing_hashed_uuid == data.get('hashed_uuid')


def assert_retrieved_eyb_lead_data(instance: EYBLead, data: dict):
    """Method to verify the retrieved EYB lead data against the EYBLead instance.

    Notably, the retrieved data has:
    - snake_case field names
    - nested objects for related fields
    - labels for choice fields.
    """
    # EYB triage fields
    assert instance.triage_hashed_uuid == data['triage_hashed_uuid']
    assert_datetimes(instance.triage_created, data['triage_created'])
    assert_datetimes(instance.triage_modified, data['triage_modified'])
    assert str(instance.sector.id) == data['sector']['id']
    assert instance.intent == data['intent']
    assert instance.intent_other == data['intent_other']
    assert str(instance.proposed_investment_region.id) == data['proposed_investment_region']['id']
    assert instance.proposed_investment_city == data['proposed_investment_city']
    assert instance.proposed_investment_location_none == data['proposed_investment_location_none']
    assert format_currency_range_string(instance.hiring, symbol='') == data['hiring']
    assert format_currency_range_string(instance.spend) == data['spend']
    assert instance.spend_other == data['spend_other']
    assert instance.is_high_value == data['is_high_value']

    # EYB user fields
    assert instance.user_hashed_uuid == data['user_hashed_uuid']
    assert_datetimes(instance.user_created, data['user_created'])
    assert_datetimes(instance.user_modified, data['user_modified'])
    assert instance.company_name == data['company_name']
    assert instance.duns_number == data['duns_number']
    assert instance.address_1 == data['address']['line_1']
    assert instance.address_2 == data['address']['line_2']
    assert instance.address_town == data['address']['town']
    assert instance.address_county == data['address']['county']
    assert str(instance.address_country.id) == data['address']['country']['id']
    assert instance.address_postcode == data['address']['postcode']
    assert instance.company_website == data['company_website']
    assert str(instance.company.id) == data['company']['id']
    assert instance.full_name == data['full_name']
    assert instance.role == data['role']
    assert instance.email == data['email']
    assert instance.telephone_number == data['telephone_number']
    assert instance.agree_terms == data['agree_terms']
    assert instance.agree_info_email == data['agree_info_email']
    assert instance.landing_timeframe == data['landing_timeframe']
    assert [
        str(ip.id) for ip in instance.investment_projects.all()
    ] == [
        data_ip['id'] for data_ip in data['investment_projects']
    ]

    # EYB marketing fields
    assert instance.utm_name == data.get('utm_name')
    assert instance.utm_source == data.get('utm_source')
    assert instance.utm_medium == data.get('utm_medium')
    assert instance.utm_content == data.get('utm_content')
    assert instance.marketing_hashed_uuid == data.get('marketing_hashed_uuid')


def assert_eyb_lead_matches_company(company: Company, eyb_lead: EYBLead):
    assert eyb_lead.duns_number == company.duns_number
    assert eyb_lead.company_name == company.name
    assert eyb_lead.sector == company.sector
    assert eyb_lead.address_1 == company.address_1
    assert eyb_lead.address_2 == company.address_2
    assert eyb_lead.address_town == company.address_town
    assert eyb_lead.address_county == company.address_county
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
