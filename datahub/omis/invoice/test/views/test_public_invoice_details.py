import pytest
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.oauth.scopes import Scope
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import (
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
)


class TestPublicGetInvoice(APITestMixin):
    """Get public invoice test case."""

    @pytest.mark.parametrize(
        'order_factory',
        (
            OrderWithAcceptedQuoteFactory,
            OrderPaidFactory,
            OrderCompleteFactory,
        ),
    )
    def test_get(self, order_factory):
        """Test a successful call to get a invoice."""
        order = order_factory()

        url = reverse(
            'api-v3:omis-public:invoice:detail',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)

        invoice = order.invoice
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'created_on': format_date_or_datetime(invoice.created_on),

            'invoice_number': invoice.invoice_number,
            'invoice_company_name': invoice.invoice_company_name,
            'invoice_address_1': invoice.invoice_address_1,
            'invoice_address_2': invoice.invoice_address_2,
            'invoice_address_county': invoice.invoice_address_county,
            'invoice_address_town': invoice.invoice_address_town,
            'invoice_address_postcode': invoice.invoice_address_postcode,
            'invoice_address_country': {
                'id': str(invoice.invoice_address_country.pk),
                'name': invoice.invoice_address_country.name,
            },
            'invoice_vat_number': invoice.invoice_vat_number,
            'payment_due_date': invoice.payment_due_date.isoformat(),

            'billing_contact_name': invoice.billing_contact_name,
            'billing_company_name': invoice.billing_company_name,
            'billing_address_1': invoice.billing_address_1,
            'billing_address_2': invoice.billing_address_2,
            'billing_address_county': invoice.billing_address_county,
            'billing_address_postcode': invoice.billing_address_postcode,
            'billing_address_town': invoice.billing_address_town,
            'billing_address_country': {
                'id': str(invoice.billing_address_country.pk),
                'name': invoice.billing_address_country.name,
            },
            'po_number': invoice.po_number,

            'vat_status': invoice.vat_status,
            'vat_number': invoice.vat_number,
            'vat_verified': invoice.vat_verified,
            'net_cost': invoice.net_cost,
            'subtotal_cost': invoice.subtotal_cost,
            'vat_cost': invoice.vat_cost,
            'total_cost': invoice.total_cost,
        }

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:omis-public:invoice:detail',
            kwargs={'public_token': ('1234-abcd-' * 5)},  # len(token) == 50
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_invoice_doesnt_exist(self):
        """Test that if the invoice doesn't exist, the endpoint returns 404."""
        order = OrderFactory(status=OrderStatus.QUOTE_ACCEPTED)
        assert not order.invoice

        url = reverse(
            'api-v3:omis-public:invoice:detail',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'order_status',
        (OrderStatus.DRAFT, OrderStatus.QUOTE_AWAITING_ACCEPTANCE, OrderStatus.CANCELLED),
    )
    def test_404_if_in_disallowed_status(self, order_status):
        """Test that if the order is not in an allowed state, the endpoint returns 404."""
        order = OrderWithAcceptedQuoteFactory(status=order_status)

        url = reverse(
            'api-v3:omis-public:invoice:detail',
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
        order = OrderWithAcceptedQuoteFactory()

        url = reverse(
            'api-v3:omis-public:invoice:detail',
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
        order = OrderWithAcceptedQuoteFactory()

        url = reverse(
            'api-v3:omis-public:invoice:detail',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=scope,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
