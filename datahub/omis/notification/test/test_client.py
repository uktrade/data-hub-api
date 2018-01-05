import itertools
from unittest import mock

import pytest

from dateutil.parser import parse as dateutil_parse
from django.conf import settings

from notifications_python_client.errors import APIError

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import synchronous_executor_submit
from datahub.omis.market.models import Market
from datahub.omis.order.test.factories import (
    OrderAssigneeCompleteFactory, OrderAssigneeFactory, OrderCompleteFactory,
    OrderFactory, OrderPaidFactory, OrderSubscriberFactory, OrderWithOpenQuoteFactory
)

from ..client import notify, send_email
from ..constants import Template

pytestmark = pytest.mark.django_db


class TestSendEmail:
    """Tests for errors with the internal send_email function."""

    @mock.patch('datahub.omis.notification.client.raven_client')
    def test_error_raises_exception(self, mock_raven_client):
        """
        Test that if an error occurs whilst sending an email,
        the exception is raised and sent to sentry.
        """
        notify_client = mock.Mock()
        notify_client.send_email_notification.side_effect = APIError()

        with pytest.raises(APIError):
            send_email(notify_client)

        assert mock_raven_client.captureException.called

    def test_override_recipient_email(self, settings):
        """
        Test that if settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL is set,
        all the emails are sent to it.
        """
        settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL = 'different_email@example.com'

        notify_client = mock.Mock()
        send_email(notify_client, email_address='test@example.com')

        notify_client.send_email_notification.assert_called_with(
            email_address='different_email@example.com'
        )

    def test_without_overriding_recipient_email(self, settings):
        """
        Test that if settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL is not set,
        all the emails are sent to the intended recipient.
        """
        settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL = ''

        notify_client = mock.Mock()
        send_email(notify_client, email_address='test@example.com')

        notify_client.send_email_notification.assert_called_with(
            email_address='test@example.com'
        )


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyOrderInfo:
    """Tests for generic notifications related to an order."""

    def test_without_primary_market(self):
        """
        Test that calling `order_info` without primary market
        (in case of some legacy orders), uses a placeholder for the market.
        """
        order = OrderFactory(primary_market_id=None)

        notify.client.reset_mock()

        notify.order_info(order, what_happened='something happened', why='to inform you')

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['personalisation']['primary market'] == 'Unknown market'

    def test_with_recipient_email_and_name(self):
        """
        Test that calling `order_info` with recipient email and name sends an email
        to the specified email addressed to the specified recipient name.
        """
        order = OrderFactory()

        notify.client.reset_mock()

        notify.order_info(
            order,
            what_happened='something happened',
            why='to inform you',
            to_email='example@example.com',
            to_name='example name'
        )

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == 'example@example.com'
        assert call_args['template_id'] == Template.generic_order_info.value
        assert call_args['personalisation']['recipient name'] == 'example name'

    def test_with_recipient_email_only(self):
        """
        Test that calling `order_info` with only recipient email sends an email
        to the specified email using the email as recipient name.
        """
        order = OrderFactory()

        notify.client.reset_mock()

        notify.order_info(
            order,
            what_happened='something happened',
            why='to inform you',
            to_email='example@example.com'
        )

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == 'example@example.com'
        assert call_args['template_id'] == Template.generic_order_info.value
        assert call_args['personalisation']['recipient name'] == 'example@example.com'

    def test_with_recipient_name_only(self):
        """
        Test that calling `order_info` with only the recipient name sends an email
        to the OMIS admin email addressed to the specified recipient name.
        """
        order = OrderFactory()

        notify.client.reset_mock()

        notify.order_info(
            order,
            what_happened='something happened',
            why='to inform you',
            to_name='example name'
        )

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == settings.OMIS_NOTIFICATION_ADMIN_EMAIL
        assert call_args['template_id'] == Template.generic_order_info.value
        assert call_args['personalisation']['recipient name'] == 'example name'


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyOrderCreated:
    """Tests for notifications sent when an order is created."""

    def test_email_sent_to_manager(self):
        """
        Test that `.order_created` sends an email to the overseas manager
        of the market related to the order just created if that is defined.
        """
        market = Market.objects.first()
        market.manager_email = 'test@test.com'
        market.save()

        order = OrderFactory(primary_market_id=market.country.pk)

        notify.client.reset_mock()

        notify.order_created(order)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == 'test@test.com'
        assert call_args['template_id'] == Template.order_created_for_post_manager.value

    def test_email_sent_to_omis_admin_if_no_manager(self):
        """
        Test that `.order_created` sends an email to the OMIS admin email
        if the market related to the order just created doesn't have any overseas
        manager defined.
        """
        market = Market.objects.first()
        market.manager_email = ''
        market.save()

        order = OrderFactory(primary_market_id=market.country.id)

        notify.client.reset_mock()

        notify.order_created(order)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == settings.OMIS_NOTIFICATION_ADMIN_EMAIL
        assert call_args['template_id'] == Template.generic_order_info.value

    def test_email_sent_to_omis_admin_if_no_market(self):
        """
        Test that `.order_created` sends an email to the OMIS admin email
        if the market related to the order does not exist.
        """
        market = Market.objects.first()
        country = market.country
        market.delete()

        order = OrderFactory(primary_market_id=country.id)

        notify.client.reset_mock()

        notify.order_created(order)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == settings.OMIS_NOTIFICATION_ADMIN_EMAIL
        assert call_args['template_id'] == Template.generic_order_info.value


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyAdviserAdded:
    """Tests for the adviser_added logic."""

    def test_adviser_notified(self):
        """
        Test that calling `adviser_added` sends an email notifying the adviser that
        they have been added to the order.
        """
        order = OrderFactory()
        adviser = AdviserFactory()
        creator = AdviserFactory()

        notify.client.reset_mock()

        notify.adviser_added(
            order=order,
            adviser=adviser,
            by=creator,
            creation_date=dateutil_parse('2017-05-18')
        )

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_added_for_adviser.value

        assert call_args['personalisation']['recipient name'] == adviser.name
        assert call_args['personalisation']['creator'] == creator.name
        assert call_args['personalisation']['creation date'] == '18/05/2017'


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyAdviserRemoved:
    """Tests for the adviser_removed logic."""

    def test_adviser_notified(self):
        """
        Test that calling `adviser_removed` sends an email notifying the adviser that
        they have been removed from the order.
        """
        order = OrderFactory()
        adviser = AdviserFactory()

        notify.client.reset_mock()

        notify.adviser_removed(order=order, adviser=adviser)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_removed_for_adviser.value

        assert call_args['personalisation']['recipient name'] == adviser.name


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyOrderPaid:
    """Tests for the order_paid logic."""

    def test_customer_notified(self):
        """
        Test that calling `order_paid` sends an email notifying the customer that
        the order has been marked as paid.
        """
        order = OrderPaidFactory()

        notify.client.reset_mock()

        notify.order_paid(order)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.order_paid_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self):
        """
        Test that calling `order_paid` sends an email to all advisers notifying them that
        the order has been marked as paid.
        """
        order = OrderPaidFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        notify.order_paid(order)

        assert notify.client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in notify.client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.order_paid_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyOrderCompleted:
    """Tests for the order_completed logic."""

    def test_advisers_notified(self):
        """
        Test that calling `order_completed` sends an email to all advisers
        notifying them that the order has been marked as completed.
        """
        order = OrderCompleteFactory(assignees=[])
        assignees = OrderAssigneeCompleteFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        notify.order_completed(order)

        assert notify.client.send_email_notification.called
        # 4 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == 4

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in notify.client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.order_completed_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyOrderCancelled:
    """Tests for the order_cancelled logic."""

    def test_customer_notified(self):
        """
        Test that calling `order_cancelled` sends an email notifying the customer that
        the order has been cancelled.
        """
        order = OrderWithOpenQuoteFactory()

        notify.client.reset_mock()

        notify.order_cancelled(order)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.order_cancelled_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self):
        """
        Test that calling `order_cancelled` sends an email to all advisers notifying them that
        the order has been cancelled.
        """
        order = OrderWithOpenQuoteFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        notify.order_cancelled(order)

        assert notify.client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in notify.client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.order_cancelled_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyQuoteGenerated:
    """Tests for the quote_generated logic."""

    def test_customer_notified(self):
        """
        Test that calling `quote_generated` sends an email notifying the customer that
        they have to accept the quote.
        """
        order = OrderWithOpenQuoteFactory()

        notify.client.reset_mock()

        notify.quote_generated(order)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.quote_sent_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self):
        """
        Test that calling `quote_generated` sends an email to all advisers notifying them that
        the quote has been sent.
        """
        order = OrderWithOpenQuoteFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        notify.quote_generated(order)

        assert notify.client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in notify.client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.quote_sent_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyQuoteAccepted:
    """Tests for the quote_accepted logic."""

    def test_customer_notified(self):
        """
        Test that calling `quote_accepted` sends an email notifying the customer that
        they have accepted the quote.
        """
        order = OrderPaidFactory()

        notify.client.reset_mock()

        notify.quote_accepted(order)

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.quote_accepted_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self):
        """
        Test that calling `quote_accepted` sends an email to all advisers notifying them that
        the quote has been accepted.
        """
        order = OrderPaidFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.client.reset_mock()

        notify.quote_accepted(order)

        assert notify.client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in notify.client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.quote_accepted_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyQuoteCancelled:
    """Tests for the quote_cancelled logic."""

    def test_customer_notified(self):
        """
        Test that calling `quote_cancelled` sends an email notifying the customer that
        the quote has been cancelled.
        """
        order = OrderFactory()

        notify.client.reset_mock()

        notify.quote_cancelled(order, by=AdviserFactory())

        assert notify.client.send_email_notification.called
        call_args = notify.client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.quote_cancelled_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self):
        """
        Test that calling `quote_cancelled` sends an email to all advisers notifying them that
        the quote has been cancelled.
        """
        order = OrderFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)
        canceller = AdviserFactory()

        notify.client.reset_mock()

        notify.quote_cancelled(order, by=canceller)

        assert notify.client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(notify.client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in notify.client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.quote_cancelled_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()
            assert call['personalisation']['canceller'] == canceller.name
