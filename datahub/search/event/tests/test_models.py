import pytest

from datahub.event.test.factories import EventFactory
from ..models import Event as ESEvent

pytestmark = pytest.mark.django_db


def test_event_dbmodel_to_dict():
    """Tests conversion of db model to dict."""
    event = EventFactory()

    result = ESEvent.dbmodel_to_dict(event)

    keys = {'id', 'event_type', 'location_type', 'address_country',
            'organiser', 'lead_team', 'teams', 'related_programmes',
            'created_on', 'modified_on', 'name', 'start_date', 'end_date',
            'address_1', 'address_2', 'address_town', 'address_county',
            'address_postcode', 'notes', 'uk_region'}

    assert set(result.keys()) == keys


def test_event_dbmodels_to_es_documents():
    """Tests conversion of db models to Elasticsearch documents."""
    events = EventFactory.create_batch(2)

    result = ESEvent.dbmodels_to_es_documents(events)

    assert len(list(result)) == len(events)
