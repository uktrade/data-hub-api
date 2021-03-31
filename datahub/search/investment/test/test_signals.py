from datetime import date, datetime
from decimal import Decimal

import pytest
import reversion

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import InvestmentProjectStage
from datahub.interaction.test.factories import InvestmentProjectInteractionFactory
from datahub.investment.project.models import InvestmentDeliveryPartner
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
    InvestmentProjectTeamMemberFactory,
)
from datahub.metadata.models import (
    Country,
    InvestmentBusinessActivity,
    InvestmentStrategicDriver,
    UKRegion,
)
from datahub.metadata.test.factories import TeamFactory
from datahub.search.investment.models import InvestmentProject
from datahub.search.query_builder import (
    get_search_by_entities_query,
)

pytestmark = pytest.mark.django_db


def search_investment_project_by_id(pk):
    """Search for an investment project with the given id"""
    return get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={'id': pk},
    ).execute()


def assert_project_search_latest_interaction(has_interaction=True, name=''):
    """
    Assert that a project on elastic search has or does not have a latest interaction.

    :param has_interaction: whether to expect the latest interaction to exist or not
    :param term: search term for elastic search
    """
    filter_data = {'name': name} if name else {}
    results = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data=filter_data,
    ).execute()
    assert len(results) == 1
    result = results[0]
    if has_interaction:
        assert result['latest_interaction'] is not None
    else:
        assert result['latest_interaction'] is None


def test_investment_project_auto_sync_to_es(es_with_signals):
    """Tests if investment project gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_project'
    InvestmentProjectFactory(
        name=test_name,
    )
    es_with_signals.indices.refresh()

    result = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={'name': test_name},
    ).execute()

    assert result.hits.total.value == 1


def test_investment_project_auto_updates_to_es(es_with_signals):
    """Tests if investment project gets synced to Elasticsearch."""
    project = InvestmentProjectFactory()
    new_test_name = 'even_harder_to_find_investment_project'
    project.name = new_test_name
    project.save()
    es_with_signals.indices.refresh()

    result = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={'name': new_test_name},
    ).execute()

    assert result.hits.total.value == 1


@pytest.fixture
def team_member():
    """Team member fixture"""
    yield InvestmentProjectTeamMemberFactory(role='Co-ordinator')


def test_investment_project_team_member_added_sync_to_es(es_with_signals, team_member):
    """Tests if investment project gets synced to Elasticsearch when a team member is added."""
    es_with_signals.indices.refresh()

    results = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={},
    ).execute()

    assert len(results) == 1
    result = results[0]

    assert len(result['team_members']) == 1
    assert result['team_members'][0]['id'] == str(team_member.adviser.id)


def test_investment_project_team_member_updated_sync_to_es(es_with_signals, team_member):
    """Tests if investment project gets synced to Elasticsearch when a team member is updated."""
    new_adviser = AdviserFactory()
    team_member.adviser = new_adviser
    team_member.save()
    es_with_signals.indices.refresh()

    results = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={},
    ).execute()

    assert len(results) == 1
    result = results[0]

    assert len(result['team_members']) == 1
    assert result['team_members'][0]['id'] == str(new_adviser.id)


def test_investment_project_team_member_deleted_sync_to_es(es_with_signals, team_member):
    """Tests if investment project gets synced to Elasticsearch when a team member is deleted."""
    team_member.delete()
    es_with_signals.indices.refresh()

    results = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={},
    ).execute()

    assert len(results) == 1
    result = results[0]

    assert len(result['team_members']) == 0


@pytest.mark.parametrize(
    'field',
    (
        'created_by',
        'client_relationship_manager',
        'project_manager',
        'project_assurance_adviser',
    ),
)
def test_investment_project_syncs_when_adviser_changes(es_with_signals, field):
    """
    Tests that when an adviser is updated, investment projects related to that adviser are
    resynced.
    """
    adviser = AdviserFactory()
    project = InvestmentProjectFactory(**{field: adviser})

    adviser.dit_team = TeamFactory()
    adviser.save()

    es_with_signals.indices.refresh()

    result = search_investment_project_by_id(project.pk)

    assert result.hits.total.value == 1
    assert result.hits[0][field]['dit_team']['id'] == str(adviser.dit_team.id)
    assert result.hits[0][field]['dit_team']['name'] == adviser.dit_team.name


def test_investment_project_syncs_when_team_member_adviser_changes(es_with_signals, team_member):
    """
    Tests that when an adviser that is a team member of an investment project is updated,
    the related investment project is resynced.
    """
    adviser = team_member.adviser

    adviser.dit_team = TeamFactory()
    adviser.save()

    es_with_signals.indices.refresh()

    result = search_investment_project_by_id(team_member.investment_project.pk)

    assert result.hits.total.value == 1
    assert result.hits[0]['team_members'][0]['dit_team']['id'] == str(adviser.dit_team.id)
    assert result.hits[0]['team_members'][0]['dit_team']['name'] == adviser.dit_team.name


def test_investment_project_interaction_updated_sync_to_es(es_with_signals):
    """Test investment project gets synced to Elasticsearch when an interaction is updated."""
    investment_project = InvestmentProjectFactory()
    interaction_date = '2018-05-05T00:00:00+00:00'
    interaction_subject = 'Did something interactive'
    new_interaction = InvestmentProjectInteractionFactory(
        investment_project=investment_project,
        date=datetime.fromisoformat(interaction_date),
        subject=interaction_subject,
    )
    es_with_signals.indices.refresh()

    assert_project_search_latest_interaction(has_interaction=True)

    results = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={},
    ).execute()

    assert len(results) == 1
    result = results[0]

    assert result['latest_interaction'] == {
        'id': str(new_interaction.id),
        'subject': interaction_subject,
        'date': interaction_date,
    }


def test_investment_project_interaction_deleted_sync_to_es(es_with_signals):
    """Test investment project gets synced to Elasticsearch when an interaction is deleted."""
    investment_project = InvestmentProjectFactory()
    interaction = InvestmentProjectInteractionFactory(
        investment_project=investment_project,
    )
    es_with_signals.indices.refresh()

    assert_project_search_latest_interaction(has_interaction=True)

    interaction.delete()
    es_with_signals.indices.refresh()

    assert_project_search_latest_interaction(has_interaction=False)


def test_investment_project_interaction_changed_sync_to_es(es_with_signals):
    """
    Test projects get synced to Elasticsearch when an interaction's project is changed.

    When an interaction's project is switched to another project, both the old
    and new project should be updated in Elasticsearch.
    """
    investment_project_a = InvestmentProjectFactory(name='alpha')
    investment_project_b = InvestmentProjectFactory(name='beta')

    with reversion.create_revision():
        interaction = InvestmentProjectInteractionFactory(
            investment_project=investment_project_a,
        )

    es_with_signals.indices.refresh()

    for project_name, has_interaction in [('alpha', True), ('beta', False)]:
        assert_project_search_latest_interaction(
            has_interaction=has_interaction,
            name=project_name,
        )

    interaction.investment_project = investment_project_b
    with reversion.create_revision():
        interaction.save()

    es_with_signals.indices.refresh()

    for project_name, has_interaction in [('alpha', False), ('beta', True)]:
        assert_project_search_latest_interaction(
            has_interaction=has_interaction,
            name=project_name,
        )


def test_incomplete_fields_syncs_when_project_changes(es_with_signals):
    """
    When project fields change, the incomplete fields should update accordingly.
    """
    project = InvestmentProjectFactory(stage_id=InvestmentProjectStage.won.value.id)
    adviser = AdviserFactory()

    es_with_signals.indices.refresh()
    result = search_investment_project_by_id(project.pk)

    assert result.hits.total.value == 1
    assert result.hits[0]['incomplete_fields'] == [
        'client_cannot_provide_total_investment',
        'number_new_jobs',
        'strategic_drivers',
        'client_requirements',
        'client_considering_other_countries',
        'project_manager',
        'project_assurance_adviser',
        'client_cannot_provide_foreign_investment',
        'government_assistance',
        'number_safeguarded_jobs',
        'r_and_d_budget',
        'non_fdi_r_and_d_budget',
        'new_tech_to_uk',
        'export_revenue',
        'address_1',
        'address_town',
        'address_postcode',
        'actual_uk_regions',
        'delivery_partners',
        'actual_land_date',
        'total_investment',
        'uk_region_locations',
        'foreign_equity_investment',
    ]

    project.client_cannot_provide_total_investment = False
    project.number_new_jobs = 3
    project.client_requirements = 'things'
    project.client_considering_other_countries = True
    project.project_manager = adviser
    project.project_assurance_adviser = adviser
    project.client_cannot_provide_foreign_investment = True
    project.government_assistance = True
    project.number_safeguarded_jobs = 10
    project.r_and_d_budget = True
    project.non_fdi_r_and_d_budget = True
    project.new_tech_to_uk = True
    project.export_revenue = True
    project.address_1 = 'Downing Street'
    project.address_town = 'London'
    project.address_postcode = 'SW1A 2AA'
    project.actual_land_date = date(2020, 1, 1)
    project.total_investment = Decimal('100.00')
    project.foreign_equity_investment = Decimal('50.00')

    project.save()

    es_with_signals.indices.refresh()
    result = search_investment_project_by_id(project.pk)

    assert result.hits[0]['incomplete_fields'] == [
        'strategic_drivers',
        'actual_uk_regions',
        'delivery_partners',
        'competitor_countries',
        'uk_region_locations',
        'average_salary',
        'associated_non_fdi_r_and_d_project',
    ]


@pytest.mark.parametrize(
    'field,get_field_values',
    (
        ('competitor_countries', lambda: Country.objects.all()[:3]),
        ('uk_region_locations', lambda: UKRegion.objects.all()[:3]),
        ('actual_uk_regions', lambda: UKRegion.objects.all()[:2]),
        ('delivery_partners', lambda: InvestmentDeliveryPartner.objects.all()[:2]),
        ('strategic_drivers', lambda: InvestmentStrategicDriver.objects.all()[:1]),
    ),
)
def test_incomplete_fields_syncs_when_m2m_changes(es_with_signals, field, get_field_values):
    """
    When an m2m field is updated, the incomplete fields should be updated accordingly.
    """
    project = InvestmentProjectFactory(
        stage_id=InvestmentProjectStage.won.value.id,
        client_considering_other_countries=True,
    )

    es_with_signals.indices.refresh()
    result = search_investment_project_by_id(project.pk)

    assert result.hits.total.value == 1
    incomplete_fields = result.hits[0]['incomplete_fields']

    assert field in incomplete_fields

    getattr(project, field).add(*get_field_values())

    es_with_signals.indices.refresh()
    result = search_investment_project_by_id(project.pk)

    assert result.hits.total.value == 1
    incomplete_fields = result.hits[0]['incomplete_fields']

    assert field not in incomplete_fields


def test_incomplete_fields_syncs_when_business_activities_changes(es_with_signals):
    """
    When business activities are updated the incomplete fields should be updated accordingly.

    Specifically, when 'other' is added as a business activity, 'other_business_activity'
    should show as an incomplete field.
    """
    project = InvestmentProjectFactory(stage_id=InvestmentProjectStage.won.value.id)
    conditional_field = 'other_business_activity'

    es_with_signals.indices.refresh()
    result = search_investment_project_by_id(project.pk)

    assert result.hits.total.value == 1
    assert conditional_field not in result.hits[0]['incomplete_fields']

    business_activities = InvestmentBusinessActivity.objects.all()
    project.business_activities.add(*business_activities)

    es_with_signals.indices.refresh()
    result = search_investment_project_by_id(project.pk)

    assert result.hits.total.value == 1
    assert conditional_field in result.hits[0]['incomplete_fields']
