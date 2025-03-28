import pytest
from opensearchpy.exceptions import NotFoundError

from datahub.event.test.factories import EventFactory
from datahub.search.event.apps import EventSearchApp

pytestmark = pytest.mark.django_db


def test_new_event_synced(opensearch_with_signals):
    """Test that new events are synced to OpenSearch."""
    event = EventFactory()
    opensearch_with_signals.indices.refresh()

    assert opensearch_with_signals.get(
        index=EventSearchApp.search_model.get_write_index(),
        id=event.pk,
    )


def test_updated_event_synced(opensearch_with_signals):
    """Test that when an event is updated it is synced to OpenSearch."""
    event = EventFactory()
    new_name = 'cat'
    event.name = new_name
    event.save()
    opensearch_with_signals.indices.refresh()

    result = opensearch_with_signals.get(
        index=EventSearchApp.search_model.get_write_index(),
        id=event.pk,
    )
    assert result['_source']['name'] == new_name


def test_deleting_event_removes_from_opensearch(opensearch_with_signals):
    event = EventFactory()

    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=EventSearchApp.search_model.get_read_alias(),
        id=event.pk,
    )
    assert doc['_source']['name'] == event.name

    event_id = event.id
    event.delete()

    opensearch_with_signals.indices.refresh()

    with pytest.raises(NotFoundError):
        doc = opensearch_with_signals.get(
            index=EventSearchApp.search_model.get_read_alias(),
            id=event_id,
        )
