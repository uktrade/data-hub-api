import pytest

from datahub.event.test.factories import EventFactory
from datahub.search.event.models import Event as SearchEvent

pytestmark = pytest.mark.django_db


def test_event_dbmodel_to_dict(opensearch):
    """Tests conversion of db model to dict."""
    event = EventFactory()

    result = SearchEvent.db_object_to_dict(event)

    keys = {
        '_document_type',
        'id',
        'event_type',
        'location_type',
        'address_country',
        'organiser',
        'lead_team',
        'teams',
        'related_programmes',
        'created_on',
        'modified_on',
        'name',
        'start_date',
        'end_date',
        'address_1',
        'address_2',
        'address_town',
        'address_county',
        'address_postcode',
        'notes',
        'uk_region',
        'service',
        'disabled_on',
    }

    assert result.keys() == keys


def test_event_dbmodels_to_documents(opensearch):
    """Tests conversion of db models to OpenSearch documents."""
    events = EventFactory.create_batch(2)

    result = SearchEvent.db_objects_to_documents(events)

    assert len(list(result)) == len(events)
