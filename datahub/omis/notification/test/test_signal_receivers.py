import pytest

from datahub.omis.order.test.factories import OrderFactory

from ..client import notify

pytestmark = pytest.mark.django_db


class TestNotifyPostSaveOrder:
    """Tests for notifications sent when signals are triggered."""

    def test_notification_on_order_created(self):
        """Test that a notification is triggered when an order is created."""
        notify.client.reset_mock()

        OrderFactory()

        assert notify.client.send_email_notification.called

    def test_no_notification_on_order_updated(self):
        """Test that no notification is triggered when saving an order."""
        order = OrderFactory()

        notify.client.reset_mock()

        order.description = 'new description'
        order.save()

        assert not notify.client.send_email_notification.called
