import uuid
from datetime import timezone
from random import choice

import factory.fuzzy
from django.utils.timezone import now

from datahub.company.ch_constants import COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING
from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import (
    Advisor,
    Company,
    CompanyExportCountry,
    CompanyExportCountryHistory,
    ExportExperienceCategory,
)
from datahub.core import constants
from datahub.core.test.factories import to_many_field
from datahub.core.test_utils import random_obj_for_model
from datahub.metadata.models import (
    Country,
    EmployeeRange,
    HeadquarterType,
    TurnoverRange,
)
from datahub.metadata.test.factories import CountryFactory, SectorFactory, TeamFactory


class AdviserFactory(factory.django.DjangoModelFactory):
    """Adviser factory."""

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    dit_team = factory.SubFactory(TeamFactory)
    email = factory.Sequence(lambda n: f'foo-{n}@bar.com')
    contact_email = factory.Faker('email')
    telephone_number = factory.Faker('phone_number')
    date_joined = now()
    sso_user_id = factory.LazyFunction(uuid.uuid4)
    sso_email_user_id = email

    class Meta:
        model = 'company.Advisor'
        django_get_or_create = ('email',)


class CompanyFactory(factory.django.DjangoModelFactory):
    """Company factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    name = factory.Faker('company')
    trading_names = factory.List(
        [
            factory.Faker('company'),
            factory.Faker('company'),
        ],
    )

    address_1 = factory.Sequence(lambda x: f'{x} Fake Lane')
    address_town = 'Woodside'
    address_postcode = factory.Faker('postcode')
    address_area_id = None
    address_country_id = constants.Country.united_kingdom.value.id

    registered_address_1 = factory.Sequence(lambda n: f'{n} Foo st.')
    registered_address_town = 'London'
    registered_address_postcode = factory.Faker('postcode')
    registered_address_country_id = constants.Country.united_kingdom.value.id

    business_type_id = BusinessTypeConstant.private_limited_company.value.id
    sector_id = factory.LazyFunction(
        lambda: choice(list(constants.Sector)).value.id,
    )
    archived = False
    uk_region_id = constants.UKRegion.england.value.id
    export_experience_category = factory.LazyFunction(
        ExportExperienceCategory.objects.order_by('?').first,
    )
    turnover_range = factory.LazyFunction(lambda: random_obj_for_model(TurnoverRange))
    employee_range = factory.LazyFunction(lambda: random_obj_for_model(EmployeeRange))
    turnover = 100
    is_turnover_estimated = True
    number_of_employees = 95
    is_number_of_employees_estimated = True
    archived_documents_url_path = factory.Faker('uri_path')
    created_on = now()
    export_segment = constants.ExportSegment.hep.value.id
    export_sub_segment = constants.ExportSubSegment.challenge.value.id
    is_out_of_business = False

    @to_many_field
    def export_to_countries(self):  # noqa: D102
        """Add support for setting `export_to_countries`.
        """
        return []

    @to_many_field
    def future_interest_countries(self):  # noqa: D102
        """Add support for setting `future_interest_countries`.
        """
        return []

    @to_many_field
    def export_countries(self):  # noqa: D102
        """Add support for setting `export_countries`.
        """
        return []

    class Params:
        hq = factory.Trait(
            headquarter_type=factory.LazyFunction(lambda: random_obj_for_model(HeadquarterType)),
        )

    class Meta:
        model = 'company.Company'


class CompanyWithAreaFactory(CompanyFactory):
    """Company factory with `address_area_id` populated"""

    address_area_id = constants.AdministrativeArea.texas.value.id


class SubsidiaryFactory(CompanyWithAreaFactory):
    """Subsidiary factory."""

    global_headquarters = factory.SubFactory(
        CompanyFactory,
        headquarter_type_id=constants.HeadquarterType.ghq.value.id,
    )


class OneListCoreTeamMemberFactory(factory.django.DjangoModelFactory):
    """One List Company Core Team member factory."""

    company = factory.SubFactory(CompanyFactory)
    adviser = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'company.OneListCoreTeamMember'


class ArchivedCompanyFactory(CompanyWithAreaFactory):
    """Factory for an archived company."""

    archived = True
    archived_on = factory.Faker('past_datetime', tzinfo=timezone.utc)
    archived_by = factory.LazyFunction(lambda: random_obj_for_model(Advisor))
    archived_reason = factory.Faker('sentence')


class DuplicateCompanyFactory(ArchivedCompanyFactory):
    """Factory for company that has been marked as a duplicate."""

    transferred_by = factory.SubFactory(AdviserFactory)
    transferred_on = factory.Faker('past_datetime', tzinfo=timezone.utc)
    transferred_to = factory.SubFactory(CompanyFactory)
    transfer_reason = Company.TransferReason.DUPLICATE


def _get_random_company_category():
    categories = [key for key, val in COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING.items() if val]
    return choice(categories).capitalize()


class ContactFactory(factory.django.DjangoModelFactory):
    """Contact factory"""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    title_id = constants.Title.wing_commander.value.id
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    company = factory.SubFactory(CompanyFactory)
    address_area_id = None
    email = 'foo@bar.com'
    job_title = factory.Faker('job')
    primary = True
    full_telephone_number = '+44 123456789'
    address_same_as_company = True
    created_on = now()
    archived_documents_url_path = factory.LazyFunction(lambda: f'/documents/{uuid.uuid4()}')
    consent_data = None
    consent_data_last_modified = None

    class Meta:
        model = 'company.Contact'


class ContactWithOwnAddressFactory(ContactFactory):
    """Factory for a contact with an address different from the contact's company."""

    address_same_as_company = False
    address_1 = factory.Faker('street_address')
    address_town = factory.Faker('city')
    address_postcode = factory.Faker('postcode')
    address_country_id = constants.Country.united_kingdom.value.id


class ContactWithOwnAreaFactory(ContactWithOwnAddressFactory):
    """Factory for a contact with an address different from the contact's
    company that includes an area
    """

    address_country_id = constants.Country.united_states.value.id
    address_area_id = constants.AdministrativeArea.texas.value.id


class ArchivedContactFactory(ContactFactory):
    """Factory for an archived contact."""

    archived = True
    archived_on = factory.Faker('past_datetime', tzinfo=timezone.utc)
    archived_by = factory.LazyFunction(lambda: random_obj_for_model(Advisor))
    archived_reason = factory.Faker('sentence')


class CompanyExportCountryFactory(factory.django.DjangoModelFactory):
    """Factory for Company export country"""

    company = factory.SubFactory(CompanyFactory)
    country = factory.Iterator(Country.objects.all())
    status = CompanyExportCountry.Status.CURRENTLY_EXPORTING
    created_by = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'company.CompanyExportCountry'


class CompanyExportCountryHistoryFactory(factory.django.DjangoModelFactory):
    """Factory for Company export country history"""

    history_id = factory.LazyFunction(uuid.uuid4)
    id = factory.LazyFunction(uuid.uuid4)
    company = factory.SubFactory(CompanyFactory)
    country = factory.Iterator(Country.objects.all())
    status = factory.fuzzy.FuzzyChoice(CompanyExportCountry.Status.values)
    history_user = factory.SubFactory(AdviserFactory)
    history_type = factory.fuzzy.FuzzyChoice(CompanyExportCountryHistory.HistoryType.values)

    class Meta:
        model = 'company.CompanyExportCountryHistory'


class OneListTierFactory(factory.django.DjangoModelFactory):
    """One List Tier factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker('company')

    class Meta:
        model = 'company.OneListTier'


class ExportExperienceFactory(factory.django.DjangoModelFactory):
    """Export experience factory"""

    class Meta:
        model = 'company.ExportExperience'


class ExportYearFactory(factory.django.DjangoModelFactory):
    """Export year factory"""

    class Meta:
        model = 'company.ExportYear'


class ExportFactory(factory.django.DjangoModelFactory):
    """Export factory"""

    company = factory.SubFactory(CompanyFactory)
    title = factory.Faker('name')
    owner = factory.SubFactory(AdviserFactory)
    estimated_export_value_years = factory.SubFactory(ExportYearFactory)
    estimated_export_value_amount = factory.fuzzy.FuzzyDecimal(1000, 100000, 0)
    estimated_win_date = now().date()
    destination_country = factory.SubFactory(CountryFactory)
    sector = factory.SubFactory(SectorFactory)
    exporter_experience = factory.SubFactory(ExportExperienceFactory)

    @to_many_field
    def contacts(self):
        return []

    @to_many_field
    def team_members(self):
        return []

    class Meta:
        model = 'company.CompanyExport'


class ObjectiveFactory(factory.django.DjangoModelFactory):
    """Objective factory"""

    company = factory.SubFactory(CompanyFactory)
    subject = factory.Faker('name')
    detail = factory.Faker('text')
    target_date = factory.Faker('future_date')
    has_blocker = factory.Faker('pybool')
    blocker_description = factory.Faker('text')
    progress = factory.Faker(
        'pyint',
        min_value=0,
        max_value=100,
        step=10,
    )

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    created_on = now()

    archived = False

    class Meta:
        model = 'company.Objective'
