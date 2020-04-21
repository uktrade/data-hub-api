import pytest

from datahub.event.test.factories import EventFactory
from datahub.search.event.apps import EventSearchApp
from datahub.search.models import DEFAULT_MAPPING_TYPE

pytestmark = pytest.mark.django_db


def test_new_event_synced(es_with_signals):
    """Test that new events are synced to ES."""
    event = EventFactory()
    es_with_signals.indices.refresh()

    assert es_with_signals.get(
        index=EventSearchApp.es_model.get_write_index(),
        doc_type=DEFAULT_MAPPING_TYPE,
        id=event.pk,
    )


def test_updated_event_synced(es_with_signals):
    """Test that when an event is updated it is synced to ES."""
    event = EventFactory()
    new_name = 'cat'
    event.name = new_name
    event.save()
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=EventSearchApp.es_model.get_write_index(),
        doc_type=DEFAULT_MAPPING_TYPE,
        id=event.pk,
    )
    assert result['_source']['name'] == new_name
