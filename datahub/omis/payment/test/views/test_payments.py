import uuid
from operator import itemgetter

import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import (
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
)
from datahub.omis.payment.constants import PaymentMethod
from datahub.omis.payment.test.factories import PaymentFactory


class TestGetPayments(APITestMixin):
    """Get payments test case."""

    def test_get(self):
        """Test a successful call to get a list of payments."""
        order = OrderPaidFactory()
        PaymentFactory.create_batch(2, order=order)
        PaymentFactory.create_batch(5)  # create some extra ones not linked to `order`

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'created_on': format_date_or_datetime(payment.created_on),
                'reference': payment.reference,
                'transaction_reference': payment.transaction_reference,
                'additional_reference': payment.additional_reference,
                'amount': payment.amount,
                'method': payment.method,
                'received_on': payment.received_on.isoformat(),
            }
            for payment in order.payments.all()
        ]

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': uuid.uuid4()})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty_list(self):
        """Test that if no payments exist, the endpoint returns an empty list."""
        order = OrderPaidFactory()
        PaymentFactory.create_batch(5)  # create some payments not linked to `order`

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


class TestCreatePayments(APITestMixin):
    """Create payments test case."""

    @freeze_time('2017-04-25 13:00:00')
    @pytest.mark.parametrize(
        'order_status',
        (
            OrderStatus.quote_accepted,
        ),
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
                    'received_on': '2017-04-20',
                },
                {
                    'transaction_reference': 'some ref2',
                    'amount': order.total_cost - 1,
                    'method': PaymentMethod.MANUAL,
                    'received_on': '2017-04-21',
                },
            ],
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_items = sorted(response.json(), key=itemgetter('transaction_reference'))
        assert response_items == [
            {
                'created_on': '2017-04-25T13:00:00Z',
                'reference': '201704250001',
                'transaction_reference': 'some ref1',
                'additional_reference': '',
                'amount': 1,
                'method': PaymentMethod.BACS,  # bacs is the default one
                'received_on': '2017-04-20',
            },
            {
                'created_on': '2017-04-25T13:00:00Z',
                'reference': '201704250002',
                'transaction_reference': 'some ref2',
                'additional_reference': '',
                'amount': order.total_cost - 1,
                'method': PaymentMethod.MANUAL,
                'received_on': '2017-04-21',
            },
        ]
        order.refresh_from_db()
        assert order.status == OrderStatus.paid
        assert order.paid_on == dateutil_parse('2017-04-21T00:00:00Z')

    @pytest.mark.parametrize(
        'data,errors',
        (
            # amount != from order total cost
            (
                [
                    {'amount': 1, 'received_on': '2017-04-20', 'method': PaymentMethod.BACS},
                    {'amount': 0, 'received_on': '2017-04-21', 'method': PaymentMethod.BACS},
                ],
                {
                    'non_field_errors': (
                        'The sum of the amounts has to be equal or greater than the order total.'
                    ),
                },
            ),
            # required fields
            (
                [
                    {'amount': 1, 'received_on': '2017-04-20', 'method': PaymentMethod.BACS},
                    {'received_on': '2017-04-21', 'method': PaymentMethod.BACS},
                    {'amount': 0, 'method': PaymentMethod.BACS},
                ],
                [
                    {},
                    {'amount': ['This field is required.']},
                    {'received_on': ['This field is required.']},
                ],
            ),
            # payment method not allowed
            (
                [
                    {'amount': 1, 'received_on': '2017-04-20', 'method': PaymentMethod.CARD},
                    {'amount': 1, 'received_on': '2017-04-20', 'method': PaymentMethod.CHEQUE},
                ],
                [
                    {'method': ['"card" is not a valid choice.']},
                    {'method': ['"cheque" is not a valid choice.']},
                ],
            ),
        ),
    )
    def test_400_validation(self, data, errors):
        """Test validation errors."""
        order = OrderWithAcceptedQuoteFactory()

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == errors

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
                    'method': PaymentMethod.BACS,
                    'received_on': '2017-04-20',
                },
                {
                    'amount': 1,
                    'method': PaymentMethod.BACS,
                    'received_on': '2017-04-21',
                },
            ],
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        'disallowed_status', (
            OrderStatus.draft,
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_409_if_order_in_disallowed_status(self, disallowed_status):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        order = OrderFactory(status=disallowed_status)

        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': order.pk})
        response = self.api_client.post(url, [])
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse('api-v3:omis:payment:collection', kwargs={'order_pk': uuid.uuid4()})
        response = self.api_client.post(url, [])
        assert response.status_code == status.HTTP_404_NOT_FOUND
