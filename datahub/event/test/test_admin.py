from datetime import datetime

from django.contrib.admin import helpers
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import AdminTestMixin
from datahub.event.test.factories import EventFactory


class TestEventAdmin(AdminTestMixin):
    """Tests event admin page."""

    def test_disable_selected_events(self):
        """Tests disable selected action."""
        events = EventFactory.create_batch(5)

        ids = [event.id for event in events]

        url = reverse('admin:event_event_changelist')
        data = {
            'action': 'disable_selected',
            helpers.ACTION_CHECKBOX_NAME: ids
        }
        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        # Check if we get confirmation page in the response.
        assert 'Are you sure you want to disable selected?' in str(response.content)

        # Make sure none of selected events has been disabled.
        for event in events:
            event.refresh_from_db()
            assert event.disabled_on is None

        # Confirm the action
        data['confirm'] = 'yes'
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_302_FOUND

        # Check if selected events have been disabled.
        for event in events:
            event.refresh_from_db()
            assert event.disabled_on is not None

    def test_enable_selected_events(self):
        """Tests enable selected action."""
        events = []
        for _ in range(5):
            events.append(
                EventFactory(
                    disabled_on=datetime.utcnow()
                )
            )

        ids = [event.id for event in events]

        url = reverse('admin:event_event_changelist')
        data = {
            'action': 'enable_selected',
            helpers.ACTION_CHECKBOX_NAME: ids
        }
        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        # Check if we get confirmation page in the response.
        assert 'Are you sure you want to enable selected?' in str(response.content)

        # Make sure none of selected events has been enabled.
        for event in events:
            event.refresh_from_db()
            assert event.disabled_on is not None

        # Confirm the action
        data['confirm'] = 'yes'
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_302_FOUND

        # Check if selected events have been enabled.
        for event in events:
            event.refresh_from_db()
            assert event.disabled_on is None
