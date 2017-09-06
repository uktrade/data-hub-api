import pytest
from django.conf import settings

from datahub.event.test.factories import EventFactory
from datahub.search.event.apps import EventSearchApp

pytestmark = pytest.mark.django_db


def test_new_event_synced(setup_es):
    """Test that new events are synced to ES."""
    event = EventFactory()
    setup_es.indices.refresh()

    assert setup_es.get(
        index=settings.ES_INDEX,
        doc_type=EventSearchApp.name,
        id=event.pk
    )


def test_updated_event_synced(setup_es):
    """Test that when an event is updated it is synced to ES."""
    event = EventFactory()
    new_name = 'cat'
    event.name = new_name
    event.save()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=settings.ES_INDEX,
        doc_type=EventSearchApp.name,
        id=event.pk
    )
    assert result['_source']['name'] == new_name
