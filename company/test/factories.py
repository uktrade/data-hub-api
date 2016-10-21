import uuid

import factory
from django.utils.timezone import now

from core import constants


class AdvisorFactory(factory.django.DjangoModelFactory):
    """Advisor factory."""

    id = factory.Sequence(lambda x: '{0}'.format(uuid.uuid4()))
    first_name = factory.Sequence(lambda x: 'name {0}'.format(x))
    last_name = factory.Sequence(lambda x: 'surname {0}'.format(x))
    dit_team_id = constants.Team.overseas_managers_iran.value.id

    class Meta:
        model = 'company.Advisor'


class CompanyFactory(factory.django.DjangoModelFactory):
    """Company factory."""

    id = factory.Sequence(lambda x: '{0}'.format(uuid.uuid4()))
    name = factory.Sequence(lambda x: 'name{0}'.format(x))
    registered_address_1 = factory.Sequence(lambda x: '{0} Foo st.'.format(x))
    registered_address_town = 'London'
    registered_address_country_id = constants.Country.united_kingdom.value.id
    business_type_id = constants.BusinessType.private_limited_company.value.id
    sector_id = constants.Sector.aerospace_assembly_aircraft.value.id
    archived = False
    uk_region_id = constants.UKRegion.england.value.id

    class Meta:
        model = 'company.Company'


class CompaniesHouseCompanyFactory(factory.django.DjangoModelFactory):
    """Companies house company factory."""

    name = factory.Sequence(lambda x: 'name{0}'.format(x))
    company_number = factory.Sequence(lambda x: x)
    registered_address_1 = factory.Sequence(lambda x: '{0} Bar st.'.format(x))
    registered_address_town = 'Rome'
    registered_address_country_id = constants.Country.italy.value.id
    incorporation_date = now()

    class Meta:
        model = 'company.CompaniesHouseCompany'


class ContactFactory(factory.django.DjangoModelFactory):
    """Contact factory"""

    id = factory.Sequence(lambda x: '{0}'.format(uuid.uuid4()))
    title_id = constants.Title.wing_commander.value.id
    first_name = factory.Sequence(lambda x: 'name {0}'.format(x))
    last_name = factory.Sequence(lambda x: 'surname {0}'.format(x))
    role_id = constants.Role.owner.value.id
    company = factory.SubFactory(CompanyFactory)
    email = 'foo@bar.com'
    primary = True
    uk_region_id = constants.UKRegion.england.value.id
    telephone_countrycode = '+44'
    telephone_number = '123456789'
    address_same_as_company = True

    class Meta:
        model = 'company.Contact'

    @factory.post_generation
    def teams(self, create, extracted, **kwargs):
        """Deal with M2M teams."""
        if not create:
            return

        if extracted:
            # a list of teams were passed in, use them
            for team in extracted:
                self.teams.add(team)


class InteractionFactory(factory.django.DjangoModelFactory):
    """Interaction factory."""

    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = 'foo'

    class Meta:
        model = 'company.Interaction'
