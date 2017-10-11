import uuid

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.omis.order.test.factories import OrderPaidFactory

from ..factories import PaymentFactory


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
        assert response.json() == {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'created_on': payment.created_on.isoformat(),
                    'reference': payment.reference,
                    'transaction_reference': payment.transaction_reference,
                    'additional_reference': payment.additional_reference,
                    'amount': payment.amount,
                    'method': payment.method,
                    'payment_received_on': payment.payment_received_on.isoformat()
                }
                for payment in order.payments.all()
            ]
        }

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
        assert response.json() == {
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }
