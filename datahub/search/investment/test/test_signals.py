import pytest

from datahub.investment.test.factories import InvestmentProjectFactory
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
        filters={'name': test_name},
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
        filters={'name': new_test_name},
        entity=InvestmentProject
    ).execute()

    assert result.hits.total == 1
