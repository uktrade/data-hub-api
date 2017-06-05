import pytest

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.search import elasticsearch

pytestmark = pytest.mark.django_db


def test_company_auto_sync_to_es(setup_data):
    """Tests if company gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_company'
    company = CompanyFactory(
        name=test_name
    )
    company.save()

    setup_data.indices.refresh()

    result = elasticsearch.get_basic_search_query(test_name, entities=('company',)).execute()

    assert result.hits.total == 1


def test_company_auto_updates_to_es(setup_data):
    """Tests if company gets updated in Elasticsearch."""
    test_name = 'very_hard_to_find_company_international'
    company = CompanyFactory(
        name=test_name
    )
    company.save()

    new_test_name = 'very_hard_to_find_company_local'
    company.name = new_test_name
    company.save()
    setup_data.indices.refresh()

    result = elasticsearch.get_basic_search_query(new_test_name, entities=('company',)).execute()

    assert result.hits.total == 1
    assert result.hits[0].id == company.id


def test_contact_auto_sync_to_es(setup_data):
    """Tests if contact gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_contact'
    contact = ContactFactory(
        first_name=test_name
    )
    contact.save()
    setup_data.indices.refresh()

    result = elasticsearch.get_basic_search_query(test_name, entities=('contact',)).execute()

    assert result.hits.total == 1


def test_contact_auto_updates_to_es(setup_data):
    """Tests if contact gets updated in Elasticsearch."""
    test_name = 'very_hard_to_find_contact_ii'
    contact = ContactFactory(
        first_name=test_name
    )
    contact.save()

    new_test_name = 'very_hard_to_find_contact_v'
    contact.first_name = new_test_name
    contact.save()
    setup_data.indices.refresh()

    result = elasticsearch.get_basic_search_query(new_test_name, entities=('contact',)).execute()

    assert result.hits.total == 1
    assert result.hits[0].id == contact.id
