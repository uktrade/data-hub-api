import factory

from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import UKRegion as UKRegionConstant
from datahub.export_win.models import EmailDeliveryStatus
from datahub.metadata.test.factories import CountryFactory, SectorFactory


class RatingFactory(factory.django.DjangoModelFactory):
    """Rating factory."""

    name = factory.Sequence(lambda n: f'name {n}')

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

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'export_win.TeamType'


class HQTeamRegionOrPostFactory(factory.django.DjangoModelFactory):
    """HQTeamRegionOrPost factory."""

    name = factory.Sequence(lambda n: f'name {n}')
    team_type = factory.SubFactory(TeamTypeFactory)

    class Meta:
        model = 'export_win.HQTeamRegionOrPost'


class WinAdviserFactory(factory.django.DjangoModelFactory):
    """WinAdviser factory."""

    adviser = factory.SubFactory(AdviserFactory)
    team_type = factory.SubFactory(TeamTypeFactory)
    hq_team = factory.SubFactory(HQTeamRegionOrPostFactory)

    class Meta:
        model = 'export_win.WinAdviser'


class WinFactory(factory.django.DjangoModelFactory):
    """Win factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    date = now()
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
    customer_location_id = UKRegionConstant.north_west.value.id
    hq_team = factory.SubFactory(HQTeamRegionOrPostFactory)
    lead_officer = factory.SubFactory(AdviserFactory)
    line_manager = factory.SubFactory(AdviserFactory)
    sector = factory.SubFactory(SectorFactory)
    team_type = factory.SubFactory(TeamTypeFactory)

    class Meta:
        model = 'export_win.Win'


class CustomerResponseFactory(factory.django.DjangoModelFactory):
    """Customer response factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    win = factory.SubFactory(WinFactory)
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

    type = factory.SubFactory(BreakdownTypeFactory)
    year = factory.fuzzy.FuzzyInteger(2022, 2050, 1)
    value = factory.fuzzy.FuzzyInteger(1000, 100000, 10)

    class Meta:
        model = 'export_win.Breakdown'


class CustomerResponseTokenFactory(factory.django.DjangoModelFactory):
    """CustomerResponseToken factory."""

    expires_on = factory.Faker('date_time_this_year', after_now=True)
    customer_response = factory.SubFactory(CustomerResponseFactory)
    email_notification_id = factory.Faker('uuid4')  # Adjust based on your requirements
    email_delivery_status = factory.Faker(
        'random_element', elements=[choice[0] for choice in EmailDeliveryStatus.choices])
    company_contact = factory.SubFactory(ContactFactory)

    class Meta:
        model = 'export_win.CustomerResponseToken'
