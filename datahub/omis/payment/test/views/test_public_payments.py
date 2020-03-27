import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import OrderFactory, OrderPaidFactory
from datahub.omis.payment.test.factories import PaymentFactory


class TestPublicGetPayments(APITestMixin):
    """Public get payments test case."""

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        order = OrderFactory()

        url = reverse(
            'api-v3:public-omis:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        response = api_client.post(url, data={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        order = OrderFactory()

        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        url = reverse(
            'api-v3:public-omis:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        response = hawk_api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_whitelisted_ip(self, public_omis_api_client):
        """Test that making a request without the whitelisted client IP returns an error."""
        order = OrderFactory()

        url = reverse(
            'api-v3:public-omis:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        public_omis_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = public_omis_api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('verb', ('post', 'patch', 'delete'))
    def test_verbs_not_allowed(self, verb, public_omis_api_client):
        """Test that makes sure the other verbs are not allowed."""
        order = OrderPaidFactory()

        url = reverse(
            'api-v3:public-omis:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        response = getattr(public_omis_api_client, verb)(url, json_={})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'order_status',
        (
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
            OrderStatus.PAID,
            OrderStatus.COMPLETE,
        ),
    )
    def test_get(self, order_status, public_omis_api_client):
        """Test a successful call to get a list of payments."""
        order = OrderFactory(status=order_status)
        PaymentFactory.create_batch(2, order=order)
        PaymentFactory.create_batch(5)  # create some extra ones not linked to `order`

        url = reverse(
            'api-v3:public-omis:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.get(url)

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

    def test_404_if_order_doesnt_exist(self, public_omis_api_client):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:public-omis:payment:collection',
            kwargs={'public_token': ('1234-abcd-' * 5)},  # len(token) == 50
        )
        response = public_omis_api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'order_status',
        (OrderStatus.DRAFT, OrderStatus.CANCELLED),
    )
    def test_404_if_in_disallowed_status(self, order_status, public_omis_api_client):
        """Test that if the order is not in an allowed state, the endpoint returns 404."""
        order = OrderFactory(status=order_status)

        url = reverse(
            'api-v3:public-omis:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
