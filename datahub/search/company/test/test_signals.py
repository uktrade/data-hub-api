import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.search.query_builder import get_basic_search_query
from ..models import Company

pytestmark = pytest.mark.django_db


def test_company_auto_sync_to_es(setup_es):
    """Tests if company gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_company'
    CompanyFactory(
        name=test_name
    )
    setup_es.indices.refresh()

    result = get_basic_search_query(test_name, entities=(Company,)).execute()

    assert result.hits.total == 1


def test_company_auto_updates_to_es(setup_es):
    """Tests if company gets updated in Elasticsearch."""
    test_name = 'very_hard_to_find_company_international'
    company = CompanyFactory(
        name=test_name
    )
    new_test_name = 'very_hard_to_find_company_local'
    company.name = new_test_name
    company.save()
    setup_es.indices.refresh()

    result = get_basic_search_query(new_test_name, entities=(Company,)).execute()

    assert result.hits.total == 1
    assert result.hits[0].id == str(company.id)
