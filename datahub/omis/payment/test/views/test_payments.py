import uuid
from operator import itemgetter
import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import (
    OrderFactory, OrderPaidFactory, OrderWithAcceptedQuoteFactory
)

from ..factories import PaymentFactory
from ...constants import PaymentMethod


class TestGetPayments(APITestMixin):
    """Get payments test case."""

    def test_get(self):
        """Test a successful call to get a list of payments."""
        order = OrderPaidFactory()
        PaymentFactory.create_batch(2, order=order)
        PaymentFactory.create_batch(5)  # create some extra ones not linked to `order`

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'created_on': payment.created_on.isoformat(),
                'reference': payment.reference,
                'transaction_reference': payment.transaction_reference,
                'additional_reference': payment.additional_reference,
                'amount': payment.amount,
                'method': payment.method,
                'received_on': payment.received_on.isoformat()
            }
            for payment in order.payments.all()
        ]

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': uuid.uuid4()})
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty_list(self):
        """Test that if no payments exist, the endpoint returns an empty list."""
        order = OrderPaidFactory()
        PaymentFactory.create_batch(5)  # create some payments not linked to `order`

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


class TestCreatePayments(APITestMixin):
    """Create payments test case."""

    @freeze_time('2017-04-25 13:00:00')
    @pytest.mark.parametrize(
        'order_status',
        (
            OrderStatus.quote_accepted,
        )
    )
    def test_create(self, order_status):
        """Test a successful call to create a list of payments."""
        order = OrderFactory(status=order_status)

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.post(
            url,
            [
                {
                    'transaction_reference': 'some ref1',
                    'amount': 1,
                    'received_on': '2017-04-20'
                },
                {
                    'transaction_reference': 'some ref2',
                    'amount': order.total_cost - 1,
                    'received_on': '2017-04-21'
                }
            ],
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_items = sorted(response.json(), key=itemgetter('transaction_reference'))
        assert response_items == [
            {
                'created_on': '2017-04-25T13:00:00',
                'reference': '201704250001',
                'transaction_reference': 'some ref1',
                'additional_reference': '',
                'amount': 1,
                'method': PaymentMethod.bacs,
                'received_on': '2017-04-20'
            },
            {
                'created_on': '2017-04-25T13:00:00',
                'reference': '201704250002',
                'transaction_reference': 'some ref2',
                'additional_reference': '',
                'amount': order.total_cost - 1,
                'method': PaymentMethod.bacs,
                'received_on': '2017-04-21'
            }
        ]

    def test_400_if_amounts_less_than_total_cost(self):
        """
        Test that if the sum of the amounts is less than order.total_cost,
        the endpoint returns 400.
        """
        order = OrderWithAcceptedQuoteFactory()

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.post(
            url,
            [
                {
                    'amount': 1,
                    'received_on': '2017-04-20'
                },
                {
                    'amount': order.total_cost - 2,
                    'received_on': '2017-04-21'
                }
            ],
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': (
                'The sum of the amounts has to be equal or '
                'greater than the order total.'
            )
        }

    def test_400_generic_validation(self):
        """Test generic validation errors."""
        order = OrderWithAcceptedQuoteFactory()

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.post(
            url,
            [
                {
                    'amount': 1,
                    'received_on': '2017-04-20'
                },
                {
                    'received_on': '2017-04-21'
                },
                {
                    'amount': order.total_cost - 1
                }
            ],
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {},
            {'amount': ['This field is required.']},
            {'received_on': ['This field is required.']}
        ]

    def test_ok_if_amounts_greater_than_total_cost(self):
        """
        Test that if the sum of the amounts is greater than order.total_cost,
        the reconciliation is successful.
        """
        order = OrderWithAcceptedQuoteFactory()

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.post(
            url,
            [
                {
                    'amount': order.total_cost,
                    'received_on': '2017-04-20'
                },
                {
                    'amount': 1,
                    'received_on': '2017-04-21'
                }
            ],
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        'disallowed_status', (
            OrderStatus.draft,
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        )
    )
    def test_409_if_order_in_disallowed_status(self, disallowed_status):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        order = OrderFactory(status=disallowed_status)

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.post(url, [], format='json')
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': uuid.uuid4()})
        response = self.api_client.post(url, [], format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
