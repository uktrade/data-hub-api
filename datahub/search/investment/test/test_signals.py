from datetime import datetime

import pytest
import reversion

from datahub.company.test.factories import AdviserFactory
from datahub.interaction.test.factories import InvestmentProjectInteractionFactory
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
    InvestmentProjectTeamMemberFactory,
)
from datahub.metadata.test.factories import TeamFactory
from datahub.search.investment.models import InvestmentProject
from datahub.search.query_builder import (
    get_search_by_entities_query,
)

pytestmark = pytest.mark.django_db


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

    result = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={'id': project.pk},
    ).execute()

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

    result = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={'id': team_member.investment_project.pk},
    ).execute()

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
