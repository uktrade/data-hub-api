from unittest import mock

import pytest

from django.conf import settings

from notifications_python_client.errors import APIError

from datahub.core.test_utils import synchronous_executor_submit
from datahub.omis.market.models import Market
from datahub.omis.order.test.factories import OrderFactory

from ..client import notify, send_email
from ..constants import Template

pytestmark = pytest.mark.django_db


class TestSendEmail:
    """Tests for errors with the internal send_email function."""

    @mock.patch('datahub.omis.notification.client.raven_client')
    def test_error_raises_exception(self, mock_raven_client, settings):
        """
        Test that if an error occurs whilst sending an email,
        the exception is raised and sent to sentry.
        """
        notify_client = mock.Mock()
        notify_client.send_email_notification.side_effect = APIError()

        with pytest.raises(APIError):
            send_email(notify_client)

        assert mock_raven_client.captureException.called


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
class TestNotifyOnOrderCreated:
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
        assert call_args['template_id'] == Template.order_created.value

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
class TestNotifyOrderInfo:
    """Tests for generic notifications related to an order."""

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
