import uuid
from random import choice

import factory
from django.utils.timezone import now, utc

from datahub.company.ch_constants import COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING
from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import Advisor, ExportExperienceCategory
from datahub.core import constants
from datahub.core.test_utils import random_obj_for_model
from datahub.metadata.models import EmployeeRange, HeadquarterType, TurnoverRange
from datahub.metadata.test.factories import TeamFactory


class AdviserFactory(factory.django.DjangoModelFactory):
    """Adviser factory."""

    id = factory.LazyFunction(uuid.uuid4)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    dit_team = factory.SubFactory(TeamFactory)
    email = factory.Sequence(lambda n: f'foo-{n}@bar.com')
    contact_email = factory.Faker('email')
    telephone_number = factory.Faker('phone_number')
    date_joined = now()

    class Meta:
        model = 'company.Advisor'
        django_get_or_create = ('email', )


class CompanyFactory(factory.django.DjangoModelFactory):
    """Company factory."""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    name = factory.Faker('company')
    alias = factory.Faker('company')
    registered_address_1 = factory.Sequence(lambda n: f'{n} Foo st.')
    registered_address_town = 'London'
    registered_address_country_id = constants.Country.united_kingdom.value.id
    trading_address_1 = factory.Sequence(lambda x: f'{x} Fake Lane')
    trading_address_town = 'Woodside'
    trading_address_country_id = constants.Country.united_kingdom.value.id
    business_type_id = BusinessTypeConstant.private_limited_company.value.id
    sector_id = constants.Sector.aerospace_assembly_aircraft.value.id
    archived = False
    uk_region_id = constants.UKRegion.england.value.id
    export_experience_category = factory.LazyFunction(
        ExportExperienceCategory.objects.order_by('?').first
    )
    turnover_range = factory.LazyFunction(lambda: random_obj_for_model(TurnoverRange))
    employee_range = factory.LazyFunction(lambda: random_obj_for_model(EmployeeRange))
    archived_documents_url_path = factory.Faker('uri_path')
    created_on = now()

    class Params:
        hq = factory.Trait(
            headquarter_type=factory.LazyFunction(lambda: random_obj_for_model(HeadquarterType)),
        )

    class Meta:
        model = 'company.Company'


class CompanyCoreTeamMemberFactory(factory.django.DjangoModelFactory):
    """Company core team member factory."""

    company = factory.SubFactory(CompanyFactory)
    adviser = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'company.CompanyCoreTeamMember'


class ArchivedCompanyFactory(CompanyFactory):
    """Factory for an archived company."""

    archived = True
    archived_on = factory.Faker('past_datetime', tzinfo=utc)
    archived_by = factory.LazyFunction(lambda: random_obj_for_model(Advisor))
    archived_reason = factory.Faker('sentence')


def _get_random_company_category():
    categories = ([key for key, val in COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING.items() if val])
    return choice(categories).capitalize()


class CompaniesHouseCompanyFactory(factory.django.DjangoModelFactory):
    """Companies house company factory."""

    name = factory.Sequence(lambda n: f'name{n}')
    company_number = factory.Sequence(str)
    company_category = factory.LazyFunction(_get_random_company_category)
    registered_address_1 = factory.Sequence(lambda n: f'{n} Bar st.')
    registered_address_town = 'Rome'
    registered_address_country_id = constants.Country.italy.value.id
    incorporation_date = factory.Faker('past_date')

    class Meta:
        model = 'company.CompaniesHouseCompany'
        django_get_or_create = ('company_number', )


class ContactFactory(factory.django.DjangoModelFactory):
    """Contact factory"""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    title_id = constants.Title.wing_commander.value.id
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    company = factory.SubFactory(CompanyFactory)
    email = 'foo@bar.com'
    job_title = factory.Faker('job')
    primary = True
    telephone_countrycode = '+44'
    telephone_number = '123456789'
    address_same_as_company = True
    created_on = now()
    contactable_by_email = True
    archived_documents_url_path = factory.Faker('uri_path')

    class Meta:
        model = 'company.Contact'


class ArchivedContactFactory(ContactFactory):
    """Factory for an archived contact."""

    archived = True
    archived_on = factory.Faker('past_datetime', tzinfo=utc)
    archived_by = factory.LazyFunction(lambda: random_obj_for_model(Advisor))
    archived_reason = factory.Faker('sentence')
