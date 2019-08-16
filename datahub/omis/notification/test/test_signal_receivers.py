import pytest
from dateutil.parser import parse as dateutil_parse

from datahub.company.test.factories import AdviserFactory
from datahub.omis.notification.constants import Template
from datahub.omis.order.models import CancellationReason
from datahub.omis.order.test.factories import (
    OrderAssigneeCompleteFactory,
    OrderAssigneeFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderSubscriberFactory,
    OrderWithAcceptedQuoteFactory,
    OrderWithOpenQuoteFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNotifyPostSaveOrder:
    """Tests for notifications sent when an order is saved/updated."""

    def test_notification_on_order_created(self, notify_client):
        """Test that a notification is triggered when an order is created."""
        OrderFactory()

        assert notify_client.send_email_notification.called

    def test_no_notification_on_order_updated(self, notify_client):
        """Test that no notification is triggered when saving an order."""
        order = OrderFactory()

        notify_client.reset_mock()

        order.description = 'new description'
        order.save()

        assert not notify_client.send_email_notification.called


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNofityPostSaveOrderAdviser:
    """Tests for notifications sent when an adviser is added to an order."""

    def test_notify_on_order_assignee_added(self, notify_client):
        """
        Test that a notification is sent to the adviser when they get assigned to an order.
        """
        order = OrderFactory(assignees=[])

        notify_client.reset_mock()

        assignee = OrderAssigneeFactory(order=order)
        assert notify_client.send_email_notification.called
        call_args = notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == assignee.adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_added_for_adviser.value

    def test_notify_on_order_subscriber_added(self, notify_client):
        """
        Test that a notification is sent to the adviser when they get subscribed to an order.
        """
        order = OrderFactory(assignees=[])

        notify_client.reset_mock()

        subscriber = OrderSubscriberFactory(order=order)
        assert notify_client.send_email_notification.called
        call_args = notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == subscriber.adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_added_for_adviser.value


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNofityPostDeleteOrderAdviser:
    """Tests for notifications sent when an adviser is removed from an order."""

    def test_notify_on_order_assignee_deleted(self, notify_client):
        """
        Test that a notification is sent to the adviser when they get removed from an order.
        """
        order = OrderFactory(assignees=[])
        assignee = OrderAssigneeFactory(order=order)

        notify_client.reset_mock()

        order.assignees.all().delete()

        assert notify_client.send_email_notification.called
        call_args = notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == assignee.adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_removed_for_adviser.value

    def test_notify_on_order_subscriber_deleted(self, notify_client):
        """
        Test that a notification is sent to the adviser when they get removed from an order.
        """
        order = OrderFactory(assignees=[])
        subscriber = OrderSubscriberFactory(order=order)

        notify_client.reset_mock()

        order.subscribers.all().delete()

        assert notify_client.send_email_notification.called
        call_args = notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == subscriber.adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_removed_for_adviser.value


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNofityPostOrderPaid:
    """Tests for notifications sent when an order is marked as paid."""

    def test_notify_on_order_paid(self, notify_client):
        """Test that a notification is triggered when an order is marked as paid."""
        order = OrderWithAcceptedQuoteFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify_client.reset_mock()

        order.mark_as_paid(
            by=AdviserFactory(),
            payments_data=[
                {
                    'amount': order.total_cost,
                    'received_on': dateutil_parse('2017-01-02').date(),
                },
            ],
        )

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify_client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify_client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.order_paid_for_customer.value,
            Template.order_paid_for_adviser.value,
            Template.order_paid_for_adviser.value,
            Template.order_paid_for_adviser.value,
        ]


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNotifyPostOrderCompleted:
    """Tests for notifications sent when an order marked as completed."""

    def test_notify_on_order_completed(self, notify_client):
        """Test that a notification is triggered when an order is marked as completed."""
        order = OrderPaidFactory(assignees=[])
        OrderAssigneeCompleteFactory.create_batch(1, order=order, is_lead=True)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify_client.reset_mock()

        order.complete(by=None)

        #  3 = assignees/subscribers
        assert len(notify_client.send_email_notification.call_args_list) == 3

        templates_called = [
            data[1]['template_id']
            for data in notify_client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.order_completed_for_adviser.value,
            Template.order_completed_for_adviser.value,
            Template.order_completed_for_adviser.value,
        ]


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNofityPostOrderCancelled:
    """Tests for notifications sent when an order is cancelled."""

    def test_notify_on_order_cancelled(self, notify_client):
        """Test that a notification is triggered when an order is cancelled."""
        order = OrderFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order, is_lead=True)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify_client.reset_mock()

        order.cancel(by=AdviserFactory(), reason=CancellationReason.objects.first())

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify_client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify_client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.order_cancelled_for_customer.value,
            Template.order_cancelled_for_adviser.value,
            Template.order_cancelled_for_adviser.value,
            Template.order_cancelled_for_adviser.value,
        ]


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNotifyPostQuoteGenerated:
    """Tests for notifications sent when a quote is generated."""

    def test_notify_on_quote_generated(self, notify_client):
        """Test that a notification is triggered when a quote is generated."""
        order = OrderFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order, is_lead=True)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify_client.reset_mock()

        order.generate_quote(by=None)

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify_client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify_client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.quote_sent_for_customer.value,
            Template.quote_sent_for_adviser.value,
            Template.quote_sent_for_adviser.value,
            Template.quote_sent_for_adviser.value,
        ]


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNotifyPostQuoteAccepted:
    """Tests for notifications sent when a quote is accepted."""

    def test_notify_on_quote_accepted(self, notify_client):
        """Test that a notification is triggered when a quote is accepted."""
        order = OrderWithOpenQuoteFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order, is_lead=True)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify_client.reset_mock()

        order.accept_quote(by=None)

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify_client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify_client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.quote_accepted_for_customer.value,
            Template.quote_accepted_for_adviser.value,
            Template.quote_accepted_for_adviser.value,
            Template.quote_accepted_for_adviser.value,
        ]


@pytest.mark.usefixtures('synchronous_thread_pool', 'synchronous_on_commit')
class TestNotifyPostQuoteCancelled:
    """Tests for notifications sent when a quote is cancelled."""

    def test_notify_on_quote_cancelled(self, notify_client):
        """Test that a notification is triggered when a quote is cancelled."""
        order = OrderWithOpenQuoteFactory(assignees=[])
        OrderAssigneeFactory.create_batch(1, order=order)
        OrderSubscriberFactory.create_batch(2, order=order)

        notify_client.reset_mock()

        order.reopen(by=AdviserFactory())

        #  1 = customer, 3 = assignees/subscribers
        assert len(notify_client.send_email_notification.call_args_list) == (3 + 1)

        templates_called = [
            data[1]['template_id']
            for data in notify_client.send_email_notification.call_args_list
        ]
        assert templates_called == [
            Template.quote_cancelled_for_customer.value,
            Template.quote_cancelled_for_adviser.value,
            Template.quote_cancelled_for_adviser.value,
            Template.quote_cancelled_for_adviser.value,
        ]
