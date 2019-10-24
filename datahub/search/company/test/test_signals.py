import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.search.company.models import Company
from datahub.search.query_builder import get_basic_search_query

pytestmark = pytest.mark.django_db


def test_company_auto_sync_to_es(es_with_signals):
    """Tests if company gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_company'
    CompanyFactory(
        name=test_name,
    )
    es_with_signals.indices.refresh()

    result = get_basic_search_query(Company, test_name).execute()

    assert result.hits.total == 1


def test_company_auto_updates_to_es(es_with_signals):
    """Tests if company gets updated in Elasticsearch."""
    test_name = 'very_hard_to_find_company_international'
    company = CompanyFactory(
        name=test_name,
    )
    new_test_name = 'very_hard_to_find_company_local'
    company.name = new_test_name
    company.save()
    es_with_signals.indices.refresh()

    result = get_basic_search_query(Company, new_test_name).execute()

    assert result.hits.total == 1
    assert result.hits[0].id == str(company.id)
