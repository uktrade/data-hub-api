import pytest

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.search.company.apps import CompanySearchApp
from datahub.search.company.models import Company
from datahub.search.query_builder import get_basic_search_query
from datahub.search.test.utils import get_documents_by_ids

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


def test_company_subsidiaries_auto_update_to_es(es_with_signals):
    """Tests if company subsidiaries get updated in Elasticsearch."""
    account_owner = AdviserFactory()
    global_headquarters = CompanyFactory(one_list_account_owner=account_owner)
    subsidiaries = CompanyFactory.create_batch(2, global_headquarters=global_headquarters)
    es_with_signals.indices.refresh()

    subsidiary_ids = [subsidiary.id for subsidiary in subsidiaries]

    result = get_documents_by_ids(
        es_with_signals,
        CompanySearchApp,
        subsidiary_ids,
    )

    expected_results = {
        (str(subsidiary_id), str(account_owner.id)) for subsidiary_id in subsidiary_ids
    }
    search_results = {
        (doc['_id'], doc['_source']['one_list_group_global_account_manager']['id'])
        for doc in result['docs']
    }

    assert len(result['docs']) == 2
    assert search_results == expected_results

    new_account_owner = AdviserFactory()
    global_headquarters.one_list_account_owner = new_account_owner
    global_headquarters.save()

    es_with_signals.indices.refresh()

    new_result = get_documents_by_ids(
        es_with_signals,
        CompanySearchApp,
        subsidiary_ids,
    )

    new_expected_results = {
        (str(subsidiary_id), str(new_account_owner.id)) for subsidiary_id in subsidiary_ids
    }
    new_search_results = {
        (doc['_id'], doc['_source']['one_list_group_global_account_manager']['id'])
        for doc in new_result['docs']
    }

    assert len(new_result['docs']) == 2
    assert new_search_results == new_expected_results
