from unittest import mock
import pytest

from datahub.core.test_utils import synchronous_executor_submit
from datahub.omis.order.test.factories import (
    OrderAssigneeFactory, OrderFactory, OrderSubscriberFactory
)

from ..client import notify
from ..constants import Template

pytestmark = pytest.mark.django_db


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
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


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyPostQuoteGenerated:
    """Tests for notifications sent when a quote is generated."""

    def test_notify_on_quote_generated(self):
        """Test that a notification is triggered when a quote is generated."""
        order = OrderFactory()

        notify.client.reset_mock()

        order.generate_quote(by=None)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['template_id'] == Template.quote_awaiting_acceptance_for_customer.value


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNofityPostSaveOrderAdviser:
    """Tests for notifications sent when an adviser is added to an order."""

    def test_notify_on_order_assignee_added(self):
        """
        Test that a notification is sent to the adviser when they get assigned to an order.
        """
        order = OrderFactory(assignees=[])

        notify.client.reset_mock()

        assignee = OrderAssigneeFactory(order=order)
        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == assignee.adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_added_for_adviser.value

    def test_notify_on_order_subscriber_added(self):
        """
        Test that a notification is sent to the adviser when they get subscribed to an order.
        """
        order = OrderFactory(assignees=[])

        notify.client.reset_mock()

        subscriber = OrderSubscriberFactory(order=order)
        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == subscriber.adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_added_for_adviser.value
