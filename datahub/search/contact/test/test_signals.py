import pytest

from datahub.company.test.factories import ContactFactory
from datahub.search import elasticsearch
from ..models import Contact

pytestmark = pytest.mark.django_db


def test_contact_auto_sync_to_es(setup_es):
    """Tests if contact gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_contact'
    ContactFactory(
        first_name=test_name
    )
    setup_es.indices.refresh()

    result = elasticsearch.get_basic_search_query(test_name, entities=(Contact,)).execute()

    assert result.hits.total == 1


def test_contact_auto_updates_to_es(setup_es):
    """Tests if contact gets updated in Elasticsearch."""
    test_name = 'very_hard_to_find_contact_ii'
    contact = ContactFactory(
        first_name=test_name
    )
    contact.save()

    new_test_name = 'very_hard_to_find_contact_v'
    contact.first_name = new_test_name
    contact.save()
    setup_es.indices.refresh()

    result = elasticsearch.get_basic_search_query(new_test_name, entities=(Contact,)).execute()

    assert result.hits.total == 1
    assert result.hits[0].id == str(contact.id)
