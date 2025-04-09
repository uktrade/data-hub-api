import hashlib
import random
import uuid
from datetime import datetime, timezone

import factory
from faker import Faker

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test.factories import to_many_field
from datahub.metadata.models import Sector

INTENT_CHOICES = [
    'SET_UP_NEW_PREMISES',
    'SET_UP_A_NEW_DISTRIBUTION_CENTRE',
    'ONWARD_SALES_AND_EXPORTS_FROM_THE_UK',
    'RESEARCH_DEVELOP_AND_COLLABORATE',
    'FIND_PEOPLE_WITH_SPECIALIST_SKILLS',
    'OTHER',
]

SPEND_CHOICES = [
    '0-499999',
    '500000-1000000',
    '1000000-2500000',
    '2500000-5000000',
    '5000000+',
]

LANDING_TIME_FRAME_CHOICES = [
    'UNDER_SIX_MONTHS',
    'SIX_TO_TWELVE_MONTHS',
    'ONE_TO_TWO_YEARS',
    'OVER_TWO_YEARS',
]

HIRING_CHOICES = [
    '1-5',
    '6-10',
    '11-20',
    '21+',
    'NO_PLANS_TO_HIRE_YET',
]


fake = Faker(locale='en_GB')
factory.Faker._DEFAULT_LOCALE = 'en_GB'


def generate_hashed_uuid():
    new_uuid = uuid.uuid4()
    hashed_uuid = hashlib.sha256(new_uuid.bytes).hexdigest()
    return hashed_uuid


class EYBLeadFactory(factory.django.DjangoModelFactory):
    """EYB Lead factory."""

    class Meta:
        model = 'investment_lead.EYBLead'

    # EYB triage fields
    triage_hashed_uuid = factory.LazyFunction(generate_hashed_uuid)
    triage_created = factory.LazyFunction(datetime.now)
    triage_modified = factory.LazyFunction(datetime.now)
    sector = factory.LazyAttribute(lambda o: random.choice(list(Sector.objects.all())))
    intent = factory.LazyAttribute(
        lambda o: random.sample(INTENT_CHOICES, k=random.randint(1, 4)),
    )
    intent_other = ''
    proposed_investment_region_id = constants.UKRegion.wales.value.id
    proposed_investment_city = 'Cardiff'
    proposed_investment_location_none = False
    hiring = factory.LazyAttribute(lambda o: random.choice(HIRING_CHOICES))
    spend = factory.LazyAttribute(lambda o: random.choice(SPEND_CHOICES))
    spend_other = ''
    is_high_value = factory.Faker('pybool')

    # EYB user fields
    user_hashed_uuid = factory.LazyFunction(generate_hashed_uuid)
    user_created = factory.LazyFunction(datetime.now)
    user_modified = factory.LazyFunction(datetime.now)
    company_name = factory.Faker('company')
    duns_number = factory.Faker('numerify', text='00#######')
    address_1 = factory.Faker('street_address')
    address_2 = factory.Faker('secondary_address')
    address_town = factory.Faker('city')
    address_country_id = constants.Country.canada.value.id
    address_postcode = factory.Faker('postcode')
    company_website = factory.Faker('url')
    company = factory.SubFactory(CompanyFactory)
    full_name = factory.Faker('name')
    role = factory.Faker('job')
    email = factory.Faker('email')
    telephone_number = factory.Faker('phone_number')
    agree_terms = factory.Faker('pybool')
    agree_info_email = factory.Faker('pybool')
    landing_timeframe = factory.LazyAttribute(
        lambda o: random.choice(LANDING_TIME_FRAME_CHOICES),
    )

    # EYB marketing fields
    utm_name = factory.Faker('pystr')
    utm_source = factory.Faker('pystr')
    utm_medium = factory.Faker('pystr')
    utm_content = factory.Faker('pystr')

    @to_many_field
    def investment_projects(self):
        """Add support for setting `investment_projects`."""
        return []
    
    @to_many_field
    def advisers(self):
        """Add support for setting `advisers`."""
        return []


def random_sector_instance():
    sectors = Sector.objects.filter(disabled_on__isnull=True)
    return random.choice(sectors)


def eyb_lead_user_record_faker(overrides: dict | None = None) -> dict:
    """Creates a fake user record."""
    data = {
        'hashedUuid': generate_hashed_uuid(),
        'created': fake.date_time_between(
            start_date='-1y',
            tzinfo=timezone.utc,
        ),
        'modified': fake.date_time_between(
            start_date='-1y',
            tzinfo=timezone.utc,
        ),
        'companyName': fake.company(),
        'dunsNumber': fake.numerify(text='00#######'),
        'addressLine1': fake.street_address(),
        'addressLine2': fake.secondary_address(),
        'town': fake.city(),
        'county': fake.word(),
        'companyLocation': fake.country_code(),
        'postcode': fake.postcode(),
        'companyWebsite': fake.url(),
        'fullName': fake.name(),
        'role': fake.job(),
        'email': fake.email(),
        'telephoneNumber': fake.phone_number(),
        'agreeTerms': fake.pybool(),
        'agreeInfoEmail': fake.pybool(),
        'landingTimeframe': random.choice(LANDING_TIME_FRAME_CHOICES),
    }
    if overrides:
        data.update(overrides)
    return data


def eyb_lead_triage_record_faker(overrides: dict | None = None) -> dict:
    """Creates a fake triage record."""
    sector = random_sector_instance()
    level_zero_segment, level_one_segment, level_two_segment = (
        Sector.get_segments_from_sector_instance(sector)
    )
    data = {
        'hashedUuid': generate_hashed_uuid(),
        'triage_created': fake.date_time_between(
            start_date='-1y',
            tzinfo=timezone.utc,
        ),
        'created': fake.date_time_between(
            start_date='-1y',
            tzinfo=timezone.utc,
        ),
        'modified': fake.date_time_between(
            start_date='-1y',
            tzinfo=timezone.utc,
        ),
        'sector': level_zero_segment,
        'sectorSub': level_one_segment,
        'sectorSubSub': level_two_segment,
        'intent': random.sample(INTENT_CHOICES, k=random.randint(1, 4)),
        'intentOther': '',
        'location': constants.UKRegion.wales.value.name,
        'locationCity': 'Cardiff',
        'locationNone': False,
        'hiring': random.choice(HIRING_CHOICES),
        'spend': random.choice(SPEND_CHOICES),
        'spendOther': '',
        'isHighValue': fake.pybool(),
    }
    if overrides:
        data.update(overrides)
    return data


def eyb_lead_marketing_record_faker(overrides: dict | None = None) -> dict:
    """Creates a fake marketing record."""
    data = {
        'name': fake.word(),
        'medium': fake.word(),
        'source': fake.word(),
        'content': fake.word(),
        'hashed_uuid': generate_hashed_uuid(),
    }
    if overrides:
        data.update(overrides)
    return data
