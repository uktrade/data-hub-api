import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
    InvestmentProjectTeamMemberFactory,
)
from datahub.metadata.test.factories import TeamFactory
from datahub.search.investment.models import InvestmentProject
from datahub.search.query_builder import (
    get_search_by_entity_query,
)

pytestmark = pytest.mark.django_db


def test_investment_project_auto_sync_to_es(es_with_signals):
    """Tests if investment project gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_project'
    InvestmentProjectFactory(
        name=test_name,
    )
    es_with_signals.indices.refresh()

    result = get_search_by_entity_query(
        InvestmentProject,
        term='',
        filter_data={'name': test_name},
    ).execute()

    assert result.hits.total == 1


def test_investment_project_auto_updates_to_es(es_with_signals):
    """Tests if investment project gets synced to Elasticsearch."""
    project = InvestmentProjectFactory()
    new_test_name = 'even_harder_to_find_investment_project'
    project.name = new_test_name
    project.save()
    es_with_signals.indices.refresh()

    result = get_search_by_entity_query(
        InvestmentProject,
        term='',
        filter_data={'name': new_test_name},
    ).execute()

    assert result.hits.total == 1


@pytest.fixture
def team_member():
    """Team member fixture"""
    yield InvestmentProjectTeamMemberFactory(role='Co-ordinator')


def test_investment_project_team_member_added_sync_to_es(es_with_signals, team_member):
    """Tests if investment project gets synced to Elasticsearch when a team member is added."""
    es_with_signals.indices.refresh()

    results = get_search_by_entity_query(
        InvestmentProject,
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

    results = get_search_by_entity_query(
        InvestmentProject,
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

    results = get_search_by_entity_query(
        InvestmentProject,
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

    result = get_search_by_entity_query(
        InvestmentProject,
        term='',
        filter_data={'id': project.pk},
    ).execute()

    assert result.hits.total == 1
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

    result = get_search_by_entity_query(
        InvestmentProject,
        term='',
        filter_data={'id': team_member.investment_project.pk},
    ).execute()

    assert result.hits.total == 1
    assert result.hits[0]['team_members'][0]['dit_team']['id'] == str(adviser.dit_team.id)
    assert result.hits[0]['team_members'][0]['dit_team']['name'] == adviser.dit_team.name
