from datetime import datetime

from django.contrib.admin import helpers
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import AdminTestMixin
from datahub.event.test.factories import EventTypeFactory


class TestEventTypeAdmin(AdminTestMixin):
    """Tests event type admin page."""

    def test_disable_selected_events(self):
        """Tests disable selected action."""
        event_types = EventTypeFactory.create_batch(5)

        ids = [event_type.id for event_type in event_types]

        url = reverse('admin:event_eventtype_changelist')
        data = {
            'action': 'disable_selected',
            helpers.ACTION_CHECKBOX_NAME: ids
        }
        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        # Check if we get confirmation page in the response.
        assert 'Are you sure you want to disable selected?' in str(response.content)

        # Make sure none of selected event types has been disabled.
        for event_type in event_types:
            event_type.refresh_from_db()
            assert event_type.disabled_on is None

        # Confirm the action
        data['confirm'] = 'yes'
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_302_FOUND

        # Check if out event types have been disabled.
        for event_type in event_types:
            event_type.refresh_from_db()
            assert event_type.disabled_on is not None

    def test_enable_selected_events(self):
        """Tests enable selected action."""
        event_types = []
        for _ in range(5):
            event_types.append(
                EventTypeFactory(
                    disabled_on=datetime.utcnow()
                )
            )

        ids = [event_type.id for event_type in event_types]

        url = reverse('admin:event_eventtype_changelist')
        data = {
            'action': 'enable_selected',
            helpers.ACTION_CHECKBOX_NAME: ids
        }
        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        # Check if we get confirmation page in the response.
        assert 'Are you sure you want to enable selected?' in str(response.content)

        # Make sure none of selected event types has been enabled.
        for event_type in event_types:
            event_type.refresh_from_db()
            assert event_type.disabled_on is not None

        # Confirm the action
        data['confirm'] = 'yes'
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_302_FOUND

        # Check if out event types have been enabled.
        for event_type in event_types:
            event_type.refresh_from_db()
            assert event_type.disabled_on is None
