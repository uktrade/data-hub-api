from unittest import mock
import pytest
from dateutil.parser import parse as dateutil_parse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import synchronous_executor_submit
from datahub.omis.order.models import CancellationReason
from datahub.omis.order.test.factories import (
    OrderAssigneeCompleteFactory, OrderAssigneeFactory, OrderFactory,
    OrderPaidFactory, OrderSubscriberFactory,
    OrderWithAcceptedQuoteFactory, OrderWithOpenQuoteFactory
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


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNofityPostOrderPaid:
    """Tests for notifications sent when an order is marked as paid."""

    def test_notify_on_order_paid(self):
        """Test that a notification is triggered when an order is marked as paid."""
        order = OrderWithAcceptedQuoteFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        order.mark_as_paid(
            by=AdviserFactory(),
            payments_data=[
                {
                    'amount': order.total_cost,
                    'received_on': dateutil_parse('2017-01-02').date()
                },
            ]
        )

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify.client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.order_paid_for_customer.value,
            Template.order_paid_for_adviser.value,
            Template.order_paid_for_adviser.value,
            Template.order_paid_for_adviser.value,
        ]


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyPostOrderCompleted:
    """Tests for notifications sent when an order marked as completed."""

    def test_notify_on_order_completed(self):
        """Test that a notification is triggered when an order is marked as completed."""
        order = OrderPaidFactory(assignees=[])
        OrderAssigneeCompleteFactory.create_batch(1, order=order, is_lead=True)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        order.complete(by=None)

        #  3 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == 3

        templates_called = [
            data[1]['template_id']
            for data in notify.client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.order_completed_for_adviser.value,
            Template.order_completed_for_adviser.value,
            Template.order_completed_for_adviser.value,
        ]


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNofityPostOrderCancelled:
    """Tests for notifications sent when an order is cancelled."""

    def test_notify_on_order_cancelled(self):
        """Test that a notification is triggered when an order is cancelled."""
        order = OrderFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order, is_lead=True)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        order.cancel(by=AdviserFactory(), reason=CancellationReason.objects.first())

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify.client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.order_cancelled_for_customer.value,
            Template.order_cancelled_for_adviser.value,
            Template.order_cancelled_for_adviser.value,
            Template.order_cancelled_for_adviser.value,
        ]


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyPostQuoteGenerated:
    """Tests for notifications sent when a quote is generated."""

    def test_notify_on_quote_generated(self):
        """Test that a notification is triggered when a quote is generated."""
        order = OrderFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order, is_lead=True)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        order.generate_quote(by=None)

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify.client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.quote_sent_for_customer.value,
            Template.quote_sent_for_adviser.value,
            Template.quote_sent_for_adviser.value,
            Template.quote_sent_for_adviser.value,
        ]


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyPostQuoteAccepted:
    """Tests for notifications sent when a quote is accepted."""

    def test_notify_on_quote_accepted(self):
        """Test that a notification is triggered when a quote is accepted."""
        order = OrderWithOpenQuoteFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order, is_lead=True)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        order.accept_quote(by=None)

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify.client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.quote_accepted_for_customer.value,
            Template.quote_accepted_for_adviser.value,
            Template.quote_accepted_for_adviser.value,
            Template.quote_accepted_for_adviser.value,
        ]


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyPostQuoteCancelled:
    """Tests for notifications sent when a quote is cancelled."""

    def test_notify_on_quote_cancelled(self):
        """Test that a notification is triggered when a quote is cancelled."""
        order = OrderWithOpenQuoteFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        order.reopen(by=AdviserFactory())

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify.client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.quote_cancelled_for_customer.value,
            Template.quote_cancelled_for_adviser.value,
            Template.quote_cancelled_for_adviser.value,
            Template.quote_cancelled_for_adviser.value,
        ]
