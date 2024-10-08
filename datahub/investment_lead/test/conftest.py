import random
from datetime import timezone

import pytest


from datahub.core import constants
from datahub.core.test_utils import create_test_user
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import (
    EYBLeadFactory,
    generate_hashed_uuid,
)
from datahub.metadata.models import (
    Country,
    Sector,
    UKRegion,
)


@pytest.fixture
def test_user_with_view_permissions():
    return create_test_user(permission_codenames=['view_eyblead'])


@pytest.fixture
def random_sector_instance():
    sectors = Sector.objects.filter(disabled_on__isnull=True)
    return random.choice(sectors)


@pytest.fixture
def eyb_lead_triage_data(faker, random_sector_instance):
    return {
        'triage_hashed_uuid': generate_hashed_uuid(),
        'triage_created': faker.date_time_between(start_date='-1y', tzinfo=timezone.utc),
        'triage_modified': faker.date_time_between(start_date='-1y', tzinfo=timezone.utc),
        'sector': random_sector_instance.segment,
        'intent': random.sample(EYBLead.IntentChoices.values, k=random.randint(1, 4)),
        'intent_other': '',
        'location': constants.UKRegion.wales.value.name,
        'location_city': 'Cardiff',
        'location_none': False,
        'hiring': random.choice(EYBLead.HiringChoices.values),
        'spend': random.choice(EYBLead.SpendChoices.values),
        'spend_other': '',
        'is_high_value': faker.pybool(),
    }


@pytest.fixture
def eyb_lead_user_data(faker):
    return {
        'user_hashed_uuid': generate_hashed_uuid(),
        'user_created': faker.date_time_between(start_date='-1y', tzinfo=timezone.utc),
        'user_modified': faker.date_time_between(start_date='-1y', tzinfo=timezone.utc),
        'company_name': faker.company(),
        'duns_number': faker.numerify(text='00#######'),
        'address_1': faker.street_address(),
        'address_2': faker.secondary_address(),
        'address_town': faker.city(),
        'address_country': faker.country_code(),
        'address_postcode': faker.postcode(),
        'company_website': faker.url(),
        'full_name': faker.name(),
        'role': faker.job(),
        'email': faker.email(),
        'telephone_number': faker.phone_number(),
        'agree_terms': faker.pybool(),
        'agree_info_email': faker.pybool(),
        'landing_timeframe': random.choice(EYBLead.LandingTimeframeChoices.values),
    }


@pytest.fixture
def eyb_lead_marketing_data():
    return {
        'utm_name': 'utm-name',
        'utm_source': 'source',
        'utm_medium': 'medium',
        'utm_content': 'content',
    }


@pytest.fixture
def eyb_lead_factory_data(
    eyb_lead_triage_data,
    eyb_lead_user_data,
    eyb_lead_marketing_data,
):
    data = {
        **eyb_lead_triage_data,
        **eyb_lead_user_data,
        **eyb_lead_marketing_data,
    }
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
