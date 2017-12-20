import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.investment.test.factories import (
    InvestmentProjectFactory, InvestmentProjectTeamMemberFactory
)
from datahub.search import elasticsearch

from ..models import InvestmentProject

pytestmark = pytest.mark.django_db


def test_investment_project_auto_sync_to_es(setup_es):
    """Tests if investment project gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_project'
    InvestmentProjectFactory(
        name=test_name
    )
    setup_es.indices.refresh()

    result = elasticsearch.get_search_by_entity_query(
        term='',
        filter_data={'name': test_name},
        entity=InvestmentProject
    ).execute()

    assert result.hits.total == 1


def test_investment_project_auto_updates_to_es(setup_es):
    """Tests if investment project gets synced to Elasticsearch."""
    project = InvestmentProjectFactory()
    new_test_name = 'even_harder_to_find_investment_project'
    project.name = new_test_name
    project.save()
    setup_es.indices.refresh()

    result = elasticsearch.get_search_by_entity_query(
        term='',
        filter_data={'name': new_test_name},
        entity=InvestmentProject
    ).execute()

    assert result.hits.total == 1


@pytest.fixture
def team_member():
    """Team member fixture"""
    yield InvestmentProjectTeamMemberFactory(role='Co-ordinator')


def test_investment_project_team_member_added_sync_to_es(setup_es, team_member):
    """Tests if investment project gets synced to Elasticsearch when a team member is added."""
    setup_es.indices.refresh()

    results = elasticsearch.get_search_by_entity_query(
        term='',
        filter_data={},
        entity=InvestmentProject,
    ).execute()

    assert len(results) == 1
    result = results[0]

    assert len(result['team_members']) == 1
    assert result['team_members'][0]['id'] == str(team_member.adviser.id)


def test_investment_project_team_member_updated_sync_to_es(setup_es, team_member):
    """Tests if investment project gets synced to Elasticsearch when a team member is updated."""
    new_adviser = AdviserFactory()
    team_member.adviser = new_adviser
    team_member.save()
    setup_es.indices.refresh()

    results = elasticsearch.get_search_by_entity_query(
        term='',
        filter_data={},
        entity=InvestmentProject,
    ).execute()

    assert len(results) == 1
    result = results[0]

    assert len(result['team_members']) == 1
    assert result['team_members'][0]['id'] == str(new_adviser.id)


def test_investment_project_team_member_deleted_sync_to_es(setup_es, team_member):
    """Tests if investment project gets synced to Elasticsearch when a team member is deleted."""
    team_member.delete()
    setup_es.indices.refresh()

    results = elasticsearch.get_search_by_entity_query(
        term='',
        filter_data={},
        entity=InvestmentProject,
    ).execute()

    assert len(results) == 1
    result = results[0]

    assert len(result['team_members']) == 0
