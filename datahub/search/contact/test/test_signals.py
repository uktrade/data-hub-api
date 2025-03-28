import pytest
from opensearchpy.exceptions import NotFoundError

from datahub.company.test.factories import ContactFactory
from datahub.search.contact.apps import ContactSearchApp
from datahub.search.contact.models import Contact
from datahub.search.query_builder import get_basic_search_query

pytestmark = pytest.mark.django_db


def test_contact_auto_sync_to_opensearch(opensearch_with_signals):
    """Tests if contact gets synced to OpenSearch."""
    test_name = 'very_hard_to_find_contact'
    ContactFactory(
        first_name=test_name,
    )
    opensearch_with_signals.indices.refresh()

    result = get_basic_search_query(Contact, test_name).execute()

    assert result.hits.total.value == 1


def test_contact_auto_updates_to_opensearch(opensearch_with_signals):
    """Tests if contact gets updated in OpenSearch."""
    test_name = 'very_hard_to_find_contact_ii'
    contact = ContactFactory(
        first_name=test_name,
    )
    contact.save()

    new_test_name = 'very_hard_to_find_contact_v'
    contact.first_name = new_test_name
    contact.save()
    opensearch_with_signals.indices.refresh()

    result = get_basic_search_query(Contact, new_test_name).execute()

    assert result.hits.total.value == 1
    assert result.hits[0].id == str(contact.id)


def test_deleting_contact_removes_from_opensearch(opensearch_with_signals):
    contact = ContactFactory()

    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=ContactSearchApp.search_model.get_read_alias(),
        id=contact.pk,
    )
    assert doc['_source']['email'] == contact.email

    contact_id = contact.id
    contact.delete()

    opensearch_with_signals.indices.refresh()

    with pytest.raises(NotFoundError):
        doc = opensearch_with_signals.get(
            index=ContactSearchApp.search_model.get_read_alias(),
            id=contact_id,
        )
