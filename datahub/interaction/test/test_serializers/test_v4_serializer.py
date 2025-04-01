import pytest

from datahub.company_activity.tests.factories import StovaEventFactory
from datahub.interaction.serializers import InteractionSerializerV4
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    EventServiceDeliveryFactory,
)


@pytest.mark.django_db
class TestInteractionSerializerV4:
    """Tests for the Company Export Serializer."""

    def test_event_is_not_none_if_interaction_has_event(self):
        """Show the event from the serializer but ensure the stova_event_id is None as this event is
        not related to a stova event.
        """
        interaction = EventServiceDeliveryFactory()

        serializer = InteractionSerializerV4(instance=interaction)
        serialized_data = serializer.data

        assert serialized_data['event']['id'] == str(interaction.event_id)
        assert serialized_data['event']['name'] == interaction.event.name
        assert serialized_data['event']['stova_event_id'] is None

    def test_event_is_not_none_if_interaction_has_event_and_event_is_stova_event(self):
        stova_event = StovaEventFactory()
        datahub_event = stova_event.datahub_event.first()
        interaction = EventServiceDeliveryFactory(event=datahub_event)

        serializer = InteractionSerializerV4(instance=interaction)
        serialized_data = serializer.data

        assert serialized_data['event']['id'] == str(datahub_event.id)
        assert serialized_data['event']['name'] == datahub_event.name

        assert str(serialized_data['event']['stova_event_id']) == str(stova_event.id)

    def test_event_is_none_if_interaction_has_no_event(self):
        interaction = CompanyInteractionFactory()

        serializer = InteractionSerializerV4(instance=interaction)
        serialized_data = serializer.data

        assert serialized_data['event'] is None
