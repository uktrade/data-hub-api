import pytest
from django.contrib.admin.models import LogEntry
from django.contrib.admin.options import IS_POPUP_VAR
from django.core.exceptions import NON_FIELD_ERRORS
from django.test.client import Client
from django.urls import reverse

from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import CancellationReason, Order, OrderPermission
from datahub.omis.order.test.factories import (
    OrderCancelledFactory,
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
    OrderWithOpenQuoteFactory,
)


class TestCancelOrderAdmin(AdminTestMixin):
    """Tests for cancelling an order via the django admin."""

    def test_403_if_not_logged_in(self):
        """Test redirect to login if the user isn't authenticated."""
        url = reverse('admin:order_order_cancel', args=(OrderFactory().pk,))

        client = Client()
        response = client.post(url, data={})

        assert response.status_code == 302
        assert response['Location'] == self.login_url_with_redirect(url)

    def test_403_if_no_permissions(self):
        """Test 403 if user doesn't have enough permissions."""
        order = OrderFactory()
        url = reverse('admin:order_order_cancel', args=(order.pk,))

        # create user with all order permissions apart from change
        user = create_test_user(
            is_staff=True,
            password=self.PASSWORD,
            permission_codenames=(
                OrderPermission.add,
                OrderPermission.delete,
                OrderPermission.view,
            ),
        )

        client = self.create_client(user=user)
        response = client.post(url, data={})
        assert response.status_code == 403

    def test_404(self):
        """Test 404 if order doesn't exist."""
        order_id = '00000000-0000-0000-0000-000000000000'
        url = reverse('admin:order_order_cancel', args=(order_id,))

        response = self.client.get(url, follow=True)
        assert response.status_code == 200
        assert [msg.message for msg in response.context['messages']] == [
            f'order with ID “{order_id}” doesn’t exist. Perhaps it was deleted?',
        ]

    def test_400_popup_not_allowed(self):
        """Test popup not allowed."""
        order = OrderFactory()
        url = reverse('admin:order_order_cancel', args=(order.pk,))

        response = self.client.get(f'{url}?{IS_POPUP_VAR}=1')
        assert response.status_code == 400

    @pytest.mark.parametrize(
        'data,errors',
        (
            (
                {'reason': ''},
                {'reason': ['This field is required.']},
            ),
            (
                {'reason': '00000000-0000-0000-0000-000000000000'},
                {'reason': [
                    'Select a valid choice. That choice is not one of the available choices.',
                ]},
            ),
        ),
    )
    def test_400_validaton_error(self, data, errors):
        """Test validation errors."""
        order = OrderFactory()
        url = reverse('admin:order_order_cancel', args=(order.pk,))

        response = self.client.post(url, data=data)
        assert response.status_code == 200
        assert response.request['PATH_INFO'] == url

        assert 'form' in response.context
        assert not response.context['form'].is_valid()
        assert response.context['form'].errors == errors

    @pytest.mark.parametrize(
        'order_factory',
        (
            OrderCompleteFactory,
            OrderCancelledFactory,
        ),
    )
    def test_400_if_in_disallowed_status(self, order_factory):
        """
        Test that the action fails if the order is not in one of the allowed statuses.
        """
        order = order_factory()
        url = reverse('admin:order_order_cancel', args=(order.pk,))

        response = self.client.get(url)
        assert response.status_code == 200

        reason = CancellationReason.objects.filter(
            disabled_on__isnull=True,
        ).order_by('?').first()

        response = self.client.post(url, data={'reason': reason.pk})
        assert response.status_code == 200
        assert response.request['PATH_INFO'] == url

        # check form in error
        assert 'form' in response.context
        assert not response.context['form'].is_valid()
        err_msg = (
            'The action cannot be performed '
            f'in the current status {order.get_status_display()}.'
        )
        assert response.context['form'].errors == {
            NON_FIELD_ERRORS: [err_msg],
        }

        # check that nothing has changed in the db
        order_from_db = Order.objects.get(pk=order.pk)
        assert order.status == order_from_db.status
        assert order.cancelled_on == order_from_db.cancelled_on
        assert order.cancelled_by == order_from_db.cancelled_by
        assert order.cancellation_reason == order_from_db.cancellation_reason

        # check no logs created
        assert not LogEntry.objects.count()

    @pytest.mark.parametrize(
        'order_factory',
        (
            OrderFactory,
            OrderWithOpenQuoteFactory,
            OrderWithAcceptedQuoteFactory,
            OrderPaidFactory,
        ),
    )
    def test_200_if_in_allowed_status(self, order_factory):
        """
        Test that the order gets cancelled if it's in one of the allowed statuses.
        """
        order = order_factory()
        url = reverse('admin:order_order_cancel', args=(order.pk,))

        response = self.client.get(url)
        assert response.status_code == 200

        reason = CancellationReason.objects.filter(
            disabled_on__isnull=True,
        ).order_by('?').first()

        response = self.client.post(url, data={'reason': reason.pk}, follow=True)
        assert response.status_code == 200
        change_url = reverse('admin:order_order_change', args=(order.pk,))
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == change_url

        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED
        assert order.cancelled_on
        assert order.cancelled_by == self.user
        assert order.cancellation_reason == reason

        log_entry = LogEntry.objects.last()
        assert log_entry.user == self.user
        assert log_entry.is_change()
        assert log_entry.object_id == str(order.pk)
        assert log_entry.get_change_message() == f'Cancelled because {reason}.'
