
import hashlib
import random
import uuid

import factory
from django.utils import timezone

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.investment_lead.models import EYBLead
from datahub.metadata.test.factories import SectorFactory


factory.Faker.override_default_locale('en_GB')


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
    triage_created = factory.LazyFunction(timezone.now)
    triage_modified = factory.LazyFunction(timezone.now)
    sector = factory.SubFactory(SectorFactory)
    sector_sub = factory.LazyAttribute(lambda o: f'{o.sector.segment}')
    intent = random.choices(EYBLead.IntentChoices.values, k=random.randint(1, 6))
    intent_other = ''
    location_id = constants.UKRegion.wales.value.id
    location_city = 'Cardiff'
    location_none = False
    hiring = random.choice(EYBLead.HiringChoices.values)
    spend = random.choice(EYBLead.SpendChoices.values)
    spend_other = ''
    is_high_value = factory.Faker('pybool')

    # EYB user fields
    user_hashed_uuid = factory.LazyFunction(generate_hashed_uuid)
    user_created = factory.LazyFunction(timezone.now)
    user_modified = factory.LazyFunction(timezone.now)
    company_name = factory.Faker('company')
    company_location_id = constants.Country.canada.value.id
    full_name = factory.Faker('name')
    role = factory.Faker('job')
    email = factory.Faker('email')
    telephone_number = factory.Faker('phone_number')
    agree_terms = factory.Faker('pybool')
    agree_info_email = factory.Faker('pybool')
    landing_timeframe = random.choice(EYBLead.LandingTimeframeChoices.values)
    company_website = factory.Faker('url')

    # Company fields
    duns_number = factory.Faker('numerify', text='00#######')
    address_1 = factory.Faker('street_address')
    address_2 = factory.Faker('secondary_address')
    address_town = factory.Faker('city')
    address_county = factory.Faker('county')
    address_area_id = constants.AdministrativeArea.alberta.value.id
    address_country_id = constants.Country.canada.value.id
    address_postcode = factory.Faker('postcode')
    company = factory.SubFactory(CompanyFactory)
