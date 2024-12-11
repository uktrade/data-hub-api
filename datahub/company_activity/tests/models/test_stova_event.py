import pytest

from datahub.company_activity.models import StovaEvent
from datahub.company_activity.tests.factories import StovaEventFactory
from datahub.event.models import Event, EventType


@pytest.mark.django_db
class TestStovaEvent:
    """Tests for the StovaEvent model."""

    def test_save(self):
        """Test model save, also creates a DataHub Event."""
        assert not Event.objects.all().exists()
        stova_event = StovaEventFactory()
        assert Event.objects.all().count() == 1

        datahub_event = Event.objects.get(stova_event_id=stova_event.id)
        assert datahub_event.name == stova_event.name
        assert datahub_event.start_date == stova_event.start_date.date()
        assert datahub_event.end_date == stova_event.end_date.date()
        assert datahub_event.address_1 == stova_event.location_address1
        assert datahub_event.address_2 == stova_event.location_address2
        assert datahub_event.address_town == stova_event.location_city
        assert datahub_event.address_county == stova_event.location_state
        assert datahub_event.address_postcode == stova_event.location_postcode
        assert datahub_event.notes == stova_event.description
        assert datahub_event.event_type.name == 'Stova - unknown event type'

        stova_event.delete()
        assert not Event.objects.all().exists()

    def test_create_or_update_datahub_event(self):
        stova_event = StovaEventFactory()

        Event.objects.all().delete()
        assert not Event.objects.all().exists()

        # Assert new event created
        stova_event.create_or_update_datahub_event()
        assert Event.objects.all().exists()
        datahub_event = Event.objects.all()[0]
        assert stova_event.name == datahub_event.name

        # Assert existing event is updated and a new event is not created, save calls the function
        stova_event.name = 'new name'
        stova_event.save()
        datahub_event.refresh_from_db()
        assert datahub_event.name == 'new name'
        assert Event.objects.all().count() == 1

    def test_get_or_create_stova_event_type(self):
        assert not EventType.objects.filter(name='Stova - unknown event type').exists()

        StovaEvent.get_or_create_stova_event_type()
        assert EventType.objects.filter(name='Stova - unknown event type').count() == 1
        event_type = EventType.objects.filter(name='Stova - unknown event type')[0]
        assert event_type.name == 'Stova - unknown event type'

        StovaEvent.get_or_create_stova_event_type()
        assert EventType.objects.filter(name='Stova - unknown event type').count() == 1
