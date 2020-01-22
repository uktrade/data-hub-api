import pytest
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.oauth.scopes import Scope
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import OrderFactory, OrderPaidFactory
from datahub.omis.payment.test.factories import PaymentFactory


class TestPublicGetPayments(APITestMixin):
    """Public get payments test case."""

    @pytest.mark.parametrize(
        'order_status',
        (
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
            OrderStatus.PAID,
            OrderStatus.COMPLETE,
        ),
    )
    def test_get(self, order_status):
        """Test a successful call to get a list of payments."""
        order = OrderFactory(status=order_status)
        PaymentFactory.create_batch(2, order=order)
        PaymentFactory.create_batch(5)  # create some extra ones not linked to `order`

        url = reverse(
            'api-v3:omis-public:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)

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
        url = reverse(
            'api-v3:omis-public:payment:collection',
            kwargs={'public_token': ('1234-abcd-' * 5)},  # len(token) == 50
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'order_status',
        (OrderStatus.DRAFT, OrderStatus.CANCELLED),
    )
    def test_404_if_in_disallowed_status(self, order_status):
        """Test that if the order is not in an allowed state, the endpoint returns 404."""
        order = OrderFactory(status=order_status)

        url = reverse(
            'api-v3:omis-public:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('verb', ('post', 'patch', 'delete'))
    def test_verbs_not_allowed(self, verb):
        """Test that makes sure the other verbs are not allowed."""
        order = OrderPaidFactory()

        url = reverse(
            'api-v3:omis-public:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = getattr(client, verb)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'scope',
        (s.value for s in Scope if s != Scope.public_omis_front_end.value),
    )
    def test_403_if_scope_not_allowed(self, scope):
        """Test that other oauth2 scopes are not allowed."""
        order = OrderPaidFactory()

        url = reverse(
            'api-v3:omis-public:payment:collection',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=scope,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
