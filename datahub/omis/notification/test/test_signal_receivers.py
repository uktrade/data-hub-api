import pytest

from datahub.omis.order.test.factories import OrderFactory

from ..client import notify

pytestmark = pytest.mark.django_db


class TestNotifyPostSaveOrder:
    """Tests for notifications sent when an order is saved/updated."""

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


class TestNotifyPostQuoteGenerated:
    """Tests for notifications sent when a quote is generated."""

    def test_notify_on_quote_generated(self):
        """Test that a notification is triggered when a quote is generated."""
        order = OrderFactory()

        notify.client.reset_mock()

        order.generate_quote(by=None)

        assert notify.client.send_email_notification.called
