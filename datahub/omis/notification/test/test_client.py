import itertools

import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import UKRegion
from datahub.omis.market.models import Market
from datahub.omis.notification.client import notify
from datahub.omis.notification.constants import Template
from datahub.omis.order.test.factories import (
    OrderAssigneeCompleteFactory,
    OrderAssigneeFactory,
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderSubscriberFactory,
    OrderWithOpenQuoteFactory,
)
from datahub.omis.region.models import UKRegionalSettings

pytestmark = pytest.mark.django_db


class TestSendEmail:
    """Tests for errors with the internal send_email function."""

    def test_override_recipient_email(self, settings, mocked_notify_client):
        """
        Test that if settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL is set,
        all the emails are sent to it.
        """
        settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL = 'different_email@example.com'

        notify._send_email(
            email_address='test@example.com',
            template_id='foobar',
            personalisation={},
        )

        mocked_notify_client.send_email_notification.assert_called_with(
            email_address='different_email@example.com',
            template_id='foobar',
            personalisation={},
        )

    def test_without_overriding_recipient_email(self, settings, mocked_notify_client):
        """
        Test that if settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL is not set,
        all the emails are sent to the intended recipient.
        """
        settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL = ''

        notify._send_email(
            email_address='test@example.com',
            template_id='foobar',
            personalisation={},
        )

        mocked_notify_client.send_email_notification.assert_called_with(
            email_address='test@example.com',
            template_id='foobar',
            personalisation={},
        )


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyOrderInfo:
    """Tests for generic notifications related to an order."""

    def test_without_primary_market(self, mocked_notify_client):
        """
        Test that calling `order_info` without primary market
        (in case of some legacy orders), uses a placeholder for the market.
        """
        order = OrderFactory(primary_market_id=None)

        notify.order_info(order, what_happened='something happened', why='to inform you')

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['personalisation']['primary market'] == 'Unknown market'

    def test_with_recipient_email_and_name(self, mocked_notify_client):
        """
        Test that calling `order_info` with recipient email and name sends an email
        to the specified email addressed to the specified recipient name.
        """
        order = OrderFactory()

        notify.order_info(
            order,
            what_happened='something happened',
            why='to inform you',
            to_email='example@example.com',
            to_name='example name',
        )

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == 'example@example.com'
        assert call_args['template_id'] == Template.generic_order_info.value
        assert call_args['personalisation']['recipient name'] == 'example name'

    def test_with_recipient_email_only(self, mocked_notify_client):
        """
        Test that calling `order_info` with only recipient email sends an email
        to the specified email using the email as recipient name.
        """
        order = OrderFactory()

        notify.order_info(
            order,
            what_happened='something happened',
            why='to inform you',
            to_email='example@example.com',
        )

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == 'example@example.com'
        assert call_args['template_id'] == Template.generic_order_info.value
        assert call_args['personalisation']['recipient name'] == 'example@example.com'

    def test_with_recipient_name_only(self, mocked_notify_client):
        """
        Test that calling `order_info` with only the recipient name sends an email
        to the OMIS admin email addressed to the specified recipient name.
        """
        order = OrderFactory()

        notify.order_info(
            order,
            what_happened='something happened',
            why='to inform you',
            to_name='example name',
        )

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == settings.OMIS_NOTIFICATION_ADMIN_EMAIL
        assert call_args['template_id'] == Template.generic_order_info.value
        assert call_args['personalisation']['recipient name'] == 'example name'


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyOrderCreated:
    """Tests for notifications sent when an order is created."""

    def test_email_sent_to_managers(self, mocked_notify_client):
        """
        Test that `.order_created` sends an email to
        - the overseas manager of the market related to the order
        - the regional managers of the UK region related to the order
        """
        market = Market.objects.first()
        market.manager_email = 'test@test.com'
        market.save()

        regional_manager_emails = ['reg1@email.com', 'reg2@email.com']
        UKRegionalSettings.objects.create(
            uk_region_id=UKRegion.london.value.id,
            manager_emails=regional_manager_emails,
        )

        order = OrderFactory(
            primary_market_id=market.country.pk,
            uk_region_id=UKRegion.london.value.id,
        )

        notify.order_created(order)

        assert mocked_notify_client.send_email_notification.call_count == 3

        send_email_call_args_list = mocked_notify_client.send_email_notification.call_args_list

        # post manager notified
        call_args = send_email_call_args_list[0][1]
        assert call_args['email_address'] == 'test@test.com'
        assert call_args['template_id'] == Template.order_created_for_post_manager.value

        # regional managers notified
        for index, call_args in enumerate(send_email_call_args_list[1:]):
            call_args = call_args[1]
            assert call_args['email_address'] == regional_manager_emails[index]
            assert call_args['template_id'] == Template.order_created_for_regional_manager.value

    def test_email_sent_to_omis_admin_if_no_manager(self, mocked_notify_client):
        """
        Test that `.order_created` sends an email to the OMIS admin email
        if the market related to the order just created doesn't have any overseas
        manager defined.
        """
        market = Market.objects.first()
        market.manager_email = ''
        market.save()

        order = OrderFactory(primary_market_id=market.country.id)

        notify.order_created(order)

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == settings.OMIS_NOTIFICATION_ADMIN_EMAIL
        assert call_args['template_id'] == Template.generic_order_info.value

    def test_email_sent_to_omis_admin_if_no_market(self, mocked_notify_client):
        """
        Test that `.order_created` sends an email to the OMIS admin email
        if the market related to the order does not exist.
        """
        market = Market.objects.first()
        country = market.country
        market.delete()

        order = OrderFactory(primary_market_id=country.id)

        notify.order_created(order)

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == settings.OMIS_NOTIFICATION_ADMIN_EMAIL
        assert call_args['template_id'] == Template.generic_order_info.value

    def test_no_email_sent_to_regions_if_region_is_null(self, mocked_notify_client):
        """
        Test that if order.uk_region is null, the regional notification does not get
        triggered.
        """
        order = OrderFactory(uk_region_id=None)

        notify.order_created(order)

        assert mocked_notify_client.send_email_notification.call_count == 1
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['template_id'] != Template.order_created_for_regional_manager.value

    def test_no_email_sent_to_regions_without_settings(self, mocked_notify_client):
        """
        Test that if there's no UKRegionalSettings record defined for order.uk_region,
        the regional notification does not get triggered.
        """
        assert not UKRegionalSettings.objects.count()
        order = OrderFactory(uk_region_id=UKRegion.london.value.id)

        notify.order_created(order)

        assert mocked_notify_client.send_email_notification.call_count == 1
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['template_id'] != Template.order_created_for_regional_manager.value

    def test_no_email_sent_to_regions_if_no_manager_email_defined(self, mocked_notify_client):
        """
        Test that if the UKRegionalSettings for the order.uk_region does not define any
        manager emails, the regional notification does not get triggered.
        """
        UKRegionalSettings.objects.create(
            uk_region_id=UKRegion.london.value.id,
            manager_emails=[],
        )

        order = OrderFactory(uk_region_id=UKRegion.london.value.id)

        notify.order_created(order)

        assert mocked_notify_client.send_email_notification.call_count == 1
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['template_id'] != Template.order_created_for_regional_manager.value


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyAdviserAdded:
    """Tests for the adviser_added logic."""

    def test_adviser_notified(self, mocked_notify_client):
        """
        Test that calling `adviser_added` sends an email notifying the adviser that
        they have been added to the order.
        """
        order = OrderFactory()
        adviser = AdviserFactory()
        creator = AdviserFactory()

        notify.adviser_added(
            order=order,
            adviser=adviser,
            by=creator,
            creation_date=dateutil_parse('2017-05-18'),
        )

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_added_for_adviser.value

        assert call_args['personalisation']['recipient name'] == adviser.name
        assert call_args['personalisation']['creator'] == creator.name
        assert call_args['personalisation']['creation date'] == '18/05/2017'


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyAdviserRemoved:
    """Tests for the adviser_removed logic."""

    def test_adviser_notified(self, mocked_notify_client):
        """
        Test that calling `adviser_removed` sends an email notifying the adviser that
        they have been removed from the order.
        """
        order = OrderFactory()
        adviser = AdviserFactory()

        notify.adviser_removed(order=order, adviser=adviser)

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == adviser.contact_email
        assert call_args['template_id'] == Template.you_have_been_removed_for_adviser.value

        assert call_args['personalisation']['recipient name'] == adviser.name


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyOrderPaid:
    """Tests for the order_paid logic."""

    def test_customer_notified(self, mocked_notify_client):
        """
        Test that calling `order_paid` sends an email notifying the customer that
        the order has been marked as paid.
        """
        order = OrderPaidFactory()

        notify.order_paid(order)

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.order_paid_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self, mocked_notify_client):
        """
        Test that calling `order_paid` sends an email to all advisers notifying them that
        the order has been marked as paid.
        """
        order = OrderPaidFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.order_paid(order)

        assert mocked_notify_client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(mocked_notify_client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in mocked_notify_client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.order_paid_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyOrderCompleted:
    """Tests for the order_completed logic."""

    def test_advisers_notified(self, mocked_notify_client):
        """
        Test that calling `order_completed` sends an email to all advisers
        notifying them that the order has been marked as completed.
        """
        order = OrderCompleteFactory(assignees=[])
        assignees = OrderAssigneeCompleteFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.order_completed(order)

        assert mocked_notify_client.send_email_notification.called
        # 4 = assignees/subscribers
        assert len(mocked_notify_client.send_email_notification.call_args_list) == 4

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in mocked_notify_client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.order_completed_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyOrderCancelled:
    """Tests for the order_cancelled logic."""

    def test_customer_notified(self, mocked_notify_client):
        """
        Test that calling `order_cancelled` sends an email notifying the customer that
        the order has been cancelled.
        """
        order = OrderWithOpenQuoteFactory()

        notify.order_cancelled(order)

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.order_cancelled_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self, mocked_notify_client):
        """
        Test that calling `order_cancelled` sends an email to all advisers notifying them that
        the order has been cancelled.
        """
        order = OrderWithOpenQuoteFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.order_cancelled(order)

        assert mocked_notify_client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(mocked_notify_client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in mocked_notify_client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.order_cancelled_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyQuoteGenerated:
    """Tests for the quote_generated logic."""

    def test_customer_notified(self, mocked_notify_client):
        """
        Test that calling `quote_generated` sends an email notifying the customer that
        they have to accept the quote.
        """
        order = OrderWithOpenQuoteFactory()

        notify.quote_generated(order)

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.quote_sent_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self, mocked_notify_client):
        """
        Test that calling `quote_generated` sends an email to all advisers notifying them that
        the quote has been sent.
        """
        order = OrderWithOpenQuoteFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.quote_generated(order)

        assert mocked_notify_client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(mocked_notify_client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in mocked_notify_client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.quote_sent_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyQuoteAccepted:
    """Tests for the quote_accepted logic."""

    def test_customer_notified(self, mocked_notify_client):
        """
        Test that calling `quote_accepted` sends an email notifying the customer that
        they have accepted the quote.
        """
        order = OrderPaidFactory()

        notify.quote_accepted(order)

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.quote_accepted_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self, mocked_notify_client):
        """
        Test that calling `quote_accepted` sends an email to all advisers notifying them that
        the quote has been accepted.
        """
        order = OrderPaidFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)

        notify.quote_accepted(order)

        assert mocked_notify_client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(mocked_notify_client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in mocked_notify_client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.quote_accepted_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()


@pytest.mark.usefixtures('synchronous_thread_pool')
class TestNotifyQuoteCancelled:
    """Tests for the quote_cancelled logic."""

    def test_customer_notified(self, mocked_notify_client):
        """
        Test that calling `quote_cancelled` sends an email notifying the customer that
        the quote has been cancelled.
        """
        order = OrderFactory()

        notify.quote_cancelled(order, by=AdviserFactory())

        assert mocked_notify_client.send_email_notification.called
        call_args = mocked_notify_client.send_email_notification.call_args_list[0][1]
        assert call_args['email_address'] == order.get_current_contact_email()
        assert call_args['template_id'] == Template.quote_cancelled_for_customer.value
        assert call_args['personalisation']['recipient name'] == order.contact.name
        assert call_args['personalisation']['embedded link'] == order.get_public_facing_url()

    def test_advisers_notified(self, mocked_notify_client):
        """
        Test that calling `quote_cancelled` sends an email to all advisers notifying them that
        the quote has been cancelled.
        """
        order = OrderFactory(assignees=[])
        assignees = OrderAssigneeFactory.create_batch(2, order=order)
        subscribers = OrderSubscriberFactory.create_batch(2, order=order)
        canceller = AdviserFactory()

        notify.quote_cancelled(order, by=canceller)

        assert mocked_notify_client.send_email_notification.called
        # 1 = customer, 4 = assignees/subscribers
        assert len(mocked_notify_client.send_email_notification.call_args_list) == (4 + 1)

        calls_by_email = {
            data['email_address']: {
                'template_id': data['template_id'],
                'personalisation': data['personalisation'],
            }
            for _, data in mocked_notify_client.send_email_notification.call_args_list
        }
        for item in itertools.chain(assignees, subscribers):
            call = calls_by_email[item.adviser.get_current_email()]
            assert call['template_id'] == Template.quote_cancelled_for_adviser.value
            assert call['personalisation']['recipient name'] == item.adviser.name
            assert call['personalisation']['embedded link'] == order.get_datahub_frontend_url()
            assert call['personalisation']['canceller'] == canceller.name
