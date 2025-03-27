import pytest
from dateutil.parser import parse as dateutil_parse
from opensearchpy.exceptions import NotFoundError

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.search.company.apps import CompanySearchApp
from datahub.search.company.models import Company
from datahub.search.query_builder import get_basic_search_query
from datahub.search.test.utils import get_documents_by_ids

pytestmark = pytest.mark.django_db


def test_company_auto_sync_to_opensearch(opensearch_with_signals):
    """Tests if company gets synced to OpenSearch."""
    test_name = 'very_hard_to_find_company'
    CompanyFactory(
        name=test_name,
    )
    opensearch_with_signals.indices.refresh()

    result = get_basic_search_query(Company, test_name).execute()

    assert result.hits.total.value == 1


def test_company_auto_updates_to_opensearch(opensearch_with_signals):
    """Tests if company gets updated in OpenSearch."""
    test_name = 'very_hard_to_find_company_international'
    company = CompanyFactory(
        name=test_name,
    )
    new_test_name = 'very_hard_to_find_company_local'
    company.name = new_test_name
    company.save()
    opensearch_with_signals.indices.refresh()

    result = get_basic_search_query(Company, new_test_name).execute()

    assert result.hits.total.value == 1
    assert result.hits[0].id == str(company.id)


def test_company_subsidiaries_auto_update_to_opensearch(opensearch_with_signals):
    """Tests if company subsidiaries get updated in OpenSearch."""
    account_owner = AdviserFactory()
    global_headquarters = CompanyFactory(one_list_account_owner=account_owner)
    subsidiaries = CompanyFactory.create_batch(2, global_headquarters=global_headquarters)
    opensearch_with_signals.indices.refresh()

    subsidiary_ids = [subsidiary.id for subsidiary in subsidiaries]

    result = get_documents_by_ids(
        opensearch_with_signals,
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

    opensearch_with_signals.indices.refresh()

    new_result = get_documents_by_ids(
        opensearch_with_signals,
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


def test_adding_interaction_updates_company(opensearch_with_signals):
    """Test that when an interaction is added, the company is synced to OpenSearch."""
    test_name = 'very_hard_to_find_company'
    company = CompanyFactory(
        name=test_name,
    )

    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=CompanySearchApp.search_model.get_read_alias(),
        id=company.pk,
    )
    assert doc['_source']['name'] == test_name
    assert doc['_source']['latest_interaction_date'] is None

    CompanyInteractionFactory(
        date=dateutil_parse('2018-04-05T00:00:00Z'),
        company=company,
    )

    opensearch_with_signals.indices.refresh()

    updated_doc = opensearch_with_signals.get(
        index=CompanySearchApp.search_model.get_read_alias(),
        id=company.pk,
    )
    assert updated_doc['_source']['name'] == test_name
    assert updated_doc['_source']['latest_interaction_date'] == '2018-04-05T00:00:00+00:00'


def test_deleting_company_removes_from_opensearch(opensearch_with_signals):
    company = CompanyFactory()

    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=CompanySearchApp.search_model.get_read_alias(),
        id=company.pk,
    )
    assert doc['_source']['name'] == company.name

    company_id = company.id
    company.delete()

    opensearch_with_signals.indices.refresh()

    with pytest.raises(NotFoundError):
        doc = opensearch_with_signals.get(
            index=CompanySearchApp.search_model.get_read_alias(),
            id=company_id,
        )
