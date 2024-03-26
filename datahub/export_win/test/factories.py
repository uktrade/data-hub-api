import random
from datetime import datetime

import factory

from dateutil.relativedelta import relativedelta

from django.utils.timezone import now

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
    ExportExperienceFactory,
)
from datahub.core.constants import (
    BreakdownType as BreakdownTypeConstant,
    BusinessPotential as BusinessPotentialConstant,
    HVC as HVCConstant,
    WinType as WinTypeConstant,
    WinUKRegion as WinUKRegionConstant,
)
from datahub.core.test.factories import to_many_field
from datahub.export_win.models import BreakdownType, EmailDeliveryStatus
from datahub.metadata.test.factories import CountryFactory, SectorFactory


class RatingFactory(factory.django.DjangoModelFactory):
    """Rating factory."""

    name = factory.Sequence(lambda n: f'name {n}')
    export_win_id = random.choice(range(0, 6, 1))

    class Meta:
        model = 'export_win.Rating'


class WithoutOurSupportFactory(factory.django.DjangoModelFactory):
    """WithoutOurSupport factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.WithoutOurSupport'


class ExperienceFactory(factory.django.DjangoModelFactory):
    """Experience factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.Experience'


class ExperienceCategoriesFactory(factory.django.DjangoModelFactory):
    """Experience Categories factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.ExperienceCategories'


class MarketingSourceFactory(factory.django.DjangoModelFactory):
    """MarketingSource factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.MarketingSource'


class BreakdownTypeFactory(factory.django.DjangoModelFactory):
    """BreakdownType factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.BreakdownType'


class ExpectedValueRelationFactory(factory.django.DjangoModelFactory):
    """ExpectedValueRelation factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.ExpectedValueRelation'


class TeamTypeFactory(factory.django.DjangoModelFactory):
    """TeamType factory."""

    name = factory.Faker('word')
    export_win_id = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.TeamType'


class HQTeamRegionOrPostFactory(factory.django.DjangoModelFactory):
    """HQTeamRegionOrPost factory."""

    name = factory.Sequence(lambda n: f'name {n}')
    team_type = factory.SubFactory(TeamTypeFactory)
    export_win_id = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.HQTeamRegionOrPost'


class HVOProgrammesFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'export_win.HVOProgrammes'


class AssociatedProgrammeFactory(factory.django.DjangoModelFactory):
    """AssociatedProgramme factory."""

    name = factory.Sequence(lambda n: f'Associated programme name {n}')
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = 'export_win.AssociatedProgramme'


class SupportTypeFactory(factory.django.DjangoModelFactory):
    """SupportType factory."""

    name = factory.Sequence(lambda n: f'support type name {n}')
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = 'export_win.SupportType'


class WinFactory(factory.django.DjangoModelFactory):
    """Win factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    date = factory.Faker('date_object')
    total_expected_export_value = factory.fuzzy.FuzzyInteger(1000, 100000, 10)
    goods_vs_services = factory.SubFactory(ExpectedValueRelationFactory)
    total_expected_non_export_value = factory.fuzzy.FuzzyInteger(1000, 100000, 10)
    total_expected_odi_value = factory.fuzzy.FuzzyInteger(1000, 100000, 10)
    is_personally_confirmed = True
    is_line_manager_confirmed = True
    complete = False
    adviser = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    country = factory.SubFactory(CountryFactory)
    customer_location_id = WinUKRegionConstant.north_west.value.id
    hq_team = factory.SubFactory(HQTeamRegionOrPostFactory)
    lead_officer = factory.SubFactory(AdviserFactory)
    lead_officer_email_address = factory.Faker('email')
    line_manager = factory.SubFactory(AdviserFactory)
    sector = factory.SubFactory(SectorFactory)
    team_type = factory.SubFactory(TeamTypeFactory)
    hvc_id = HVCConstant.western_europe_aid_funded_business.value.id
    export_experience = factory.SubFactory(ExportExperienceFactory)
    name_of_customer_confidential = False
    business_potential_id = BusinessPotentialConstant.high_export_potential.value.id
    type_id = WinTypeConstant.both.value.id

    @to_many_field
    def associated_programme(self):  # noqa: D102
        """
        Add support for setting `associated_programme`.
        """
        return []

    @to_many_field
    def type_of_support(self):  # noqa: D102
        """
        Add support for setting `type_of_support`.
        """
        return []

    @to_many_field
    def company_contacts(self):  # noqa: D102
        """
        Add support for setting `company_contacts`.
        """
        return []

    @to_many_field
    def team_members(self):  # noqa: D102
        """
        Add support for setting `team_members`.
        """
        return []

    class Meta:
        model = 'export_win.Win'


class WinAdviserFactory(factory.django.DjangoModelFactory):
    """WinAdviser factory."""

    created_on = now()

    adviser = factory.SubFactory(AdviserFactory)
    team_type = factory.SubFactory(TeamTypeFactory)
    hq_team = factory.SubFactory(HQTeamRegionOrPostFactory)
    win = factory.SubFactory(WinFactory)

    class Meta:
        model = 'export_win.WinAdviser'


class CustomerResponseFactory(factory.django.DjangoModelFactory):
    """Customer response factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    win = factory.SubFactory(WinFactory)
    agree_with_win = None
    responded_on = None
    case_study_willing = False
    our_support = factory.SubFactory(RatingFactory)
    access_to_contacts = factory.SubFactory(RatingFactory)
    access_to_information = factory.SubFactory(RatingFactory)
    improved_profile = factory.SubFactory(RatingFactory)
    gained_confidence = factory.SubFactory(RatingFactory)
    developed_relationships = factory.SubFactory(RatingFactory)
    overcame_problem = factory.SubFactory(RatingFactory)
    expected_portion_without_help = factory.SubFactory(WithoutOurSupportFactory)
    last_export = factory.SubFactory(ExperienceFactory)
    marketing_source = factory.SubFactory(MarketingSourceFactory)

    class Meta:
        model = 'export_win.CustomerResponse'


class BreakdownFactory(factory.django.DjangoModelFactory):
    """Breakdown factory."""

    win = factory.SubFactory(WinFactory)
    year = factory.fuzzy.FuzzyInteger(2022, 2050, 1)
    value = factory.fuzzy.FuzzyInteger(1000, 100000, 10)

    class Meta:
        model = 'export_win.Breakdown'

    @factory.lazy_attribute
    def type(self):
        breakdown_types = [breakdown_type.value.id for breakdown_type in BreakdownTypeConstant]
        selected_id = random.choice(breakdown_types)
        return BreakdownType.objects.get(id=selected_id)


class CustomerResponseTokenFactory(factory.django.DjangoModelFactory):
    """CustomerResponseToken factory."""

    created_on = now()
    expires_on = factory.LazyFunction(lambda: datetime.utcnow() + relativedelta(days=7))
    customer_response = factory.SubFactory(CustomerResponseFactory)
    email_notification_id = factory.Faker('uuid4')  # Adjust based on your requirements
    email_delivery_status = factory.Faker(
        'random_element', elements=[choice[0] for choice in EmailDeliveryStatus.choices])
    company_contact = factory.SubFactory(ContactFactory)

    class Meta:
        model = 'export_win.CustomerResponseToken'


class LegacyExportWinsToDataHubCompanyFactory(factory.django.DjangoModelFactory):
    """LegacyExportWinsToDataHubCompany factory."""

    id = factory.Faker('uuid4')
    company = factory.SubFactory(CompanyFactory)

    class Meta:
        model = 'export_win.LegacyExportWinsToDataHubCompany'


class HVCFactory(factory.django.DjangoModelFactory):
    """HVC factory."""

    financial_year = factory.Sequence(lambda n: n)

    class Meta:
        model = 'export_win.HVC'
