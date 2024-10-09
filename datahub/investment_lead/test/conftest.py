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


def get_segments_from_sector_instance(sector: Sector) -> tuple[
    str, str | None, str | None,
]:
    """Splits a sector name into individual segments and returns a tuple of segments.

    If a sector is a level zero or one, the level one and two segments will
    be None where applicable.

    This function is tailored to a max of three levels.
    """
    segments = sector.name.split(' : ')
    return tuple(segments[i] if i < len(segments) else None for i in range(3))


@pytest.fixture
def eyb_lead_triage_data(faker, random_sector_instance):
    level_zero_segment, level_one_segment, level_two_segment = get_segments_from_sector_instance(
        random_sector_instance,
    )
    return {
        'hashedUuid': generate_hashed_uuid(),
        'created': faker.date_time_between(
            start_date='-1y', tzinfo=timezone.utc,
        ),
        'modified': faker.date_time_between(
            start_date='-1y', tzinfo=timezone.utc,
        ),
        'sector': level_zero_segment,
        'sectorSub': level_one_segment,
        'sectorSubSub': level_two_segment,
        'intent': random.sample(EYBLead.IntentChoices.values, k=random.randint(1, 4)),
        'intentOther': '',
        'location': constants.UKRegion.wales.value.name,
        'locationCity': 'Cardiff',
        'locationNone': False,
        'hiring': random.choice(EYBLead.HiringChoices.values),
        'spend': random.choice(EYBLead.SpendChoices.values),
        'spendOther': '',
        'isHighValue': faker.pybool(),
    }


@pytest.fixture
def eyb_lead_user_data(faker):
    return {
        'hashedUuid': generate_hashed_uuid(),
        'created': faker.date_time_between(
            start_date='-1y', tzinfo=timezone.utc,
        ),
        'modified': faker.date_time_between(
            start_date='-1y', tzinfo=timezone.utc,
        ),
        'companyName': faker.company(),
        'dunsNumber': faker.numerify(text='00#######'),
        'addressLine1': faker.street_address(),
        'addressLine2': faker.secondary_address(),
        'town': faker.city(),
        'companyLocation': faker.country_code(),
        'postcode': faker.postcode(),
        'companyWebsite': faker.url(),
        'fullName': faker.name(),
        'role': faker.job(),
        'email': faker.email(),
        'telephoneNumber': faker.phone_number(),
        'agreeTerms': faker.pybool(),
        'agreeInfoEmail': faker.pybool(),
        'landingTimeframe': random.choice(EYBLead.LandingTimeframeChoices.values),
    }


@pytest.fixture
def eyb_lead_factory_overrides():
    mining_sector = Sector.objects.get(
        pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
    )
    wales_region = UKRegion.objects.get(
        pk=constants.UKRegion.wales.value.id,
    )
    canada_country = Country.objects.get(
        pk=constants.Country.canada.value.id,
    )
    overrides = {
        'sector': mining_sector,
        'location': wales_region,
        'address_country': canada_country,
    }
    return overrides


@pytest.fixture
def eyb_lead_instance_from_db(eyb_lead_factory_overrides):
    eyb_lead_factory = EYBLeadFactory(**eyb_lead_factory_overrides)
    return EYBLead.objects.get(pk=eyb_lead_factory.pk)
