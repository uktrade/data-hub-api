import uuid

import factory
from django.utils.timezone import now

from datahub.core import constants


class AdviserFactory(factory.django.DjangoModelFactory):
    """Adviser factory."""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
    first_name = factory.Sequence(lambda n: f'name {n}')
    last_name = factory.Sequence(lambda n: f'surname {n}')
    dit_team_id = constants.Team.healthcare_uk.value.id
    email = factory.Sequence(lambda n: f'foo-{n}@bar.com')
    date_joined = now()

    class Meta:
        model = 'company.Advisor'
        django_get_or_create = ('email', )


class CompanyFactory(factory.django.DjangoModelFactory):
    """Company factory."""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f'name{n}')
    registered_address_1 = factory.Sequence(lambda n: f'{n} Foo st.')
    registered_address_town = 'London'
    registered_address_country_id = constants.Country.united_kingdom.value.id
    trading_address_1 = factory.Sequence(lambda x: f'{x} Fake Lane')
    trading_address_town = 'Woodside'
    trading_address_country_id = constants.Country.united_kingdom.value.id
    business_type_id = constants.BusinessType.private_limited_company.value.id
    sector_id = constants.Sector.aerospace_assembly_aircraft.value.id
    archived = False
    uk_region_id = constants.UKRegion.england.value.id
    created_on = now()

    class Meta:
        model = 'company.Company'


class CompaniesHouseCompanyFactory(factory.django.DjangoModelFactory):
    """Companies house company factory."""

    name = factory.Sequence(lambda n: f'name{n}')
    company_number = factory.Sequence(str)
    registered_address_1 = factory.Sequence(lambda n: f'{n} Bar st.')
    registered_address_town = 'Rome'
    registered_address_country_id = constants.Country.italy.value.id
    incorporation_date = now()

    class Meta:
        model = 'company.CompaniesHouseCompany'
        django_get_or_create = ('company_number', )


class ContactFactory(factory.django.DjangoModelFactory):
    """Contact factory"""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
    title_id = constants.Title.wing_commander.value.id
    first_name = factory.Sequence(lambda n: 'name {n}')
    last_name = factory.Sequence(lambda n: 'surname {n}')
    company = factory.SubFactory(CompanyFactory)
    email = 'foo@bar.com'
    primary = True
    telephone_countrycode = '+44'
    telephone_number = '123456789'
    address_same_as_company = True
    created_on = now()
    contactable_by_email = True

    class Meta:
        model = 'company.Contact'
