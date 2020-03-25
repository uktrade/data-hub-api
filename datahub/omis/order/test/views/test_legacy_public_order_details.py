import pytest
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.oauth.scopes import Scope
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import OrderFactory, OrderWithCancelledQuoteFactory
from datahub.omis.quote.test.factories import QuoteFactory


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestViewPublicOrderDetails(APITestMixin):
    """Tests for the pubic facing order endpoints."""

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
        """Test getting an existing order by `public_token`."""
        order = OrderFactory(
            quote=QuoteFactory(),
            status=order_status,
        )

        url = reverse(
            'api-v3:omis-public:order:detail',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'public_token': order.public_token,
            'reference': order.reference,
            'status': order.status,
            'created_on': format_date_or_datetime(order.created_on),
            'company': {
                'id': str(order.company.pk),
                'name': order.company.name,
            },
            'contact': {
                'id': str(order.contact.pk),
                'name': order.contact.name,
            },
            'primary_market': {
                'id': str(order.primary_market.id),
                'name': order.primary_market.name,
            },
            'uk_region': {
                'id': str(order.uk_region.id),
                'name': order.uk_region.name,
            },
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'vat_status': order.vat_status,
            'vat_number': order.vat_number,
            'vat_verified': order.vat_verified,
            'po_number': order.po_number,
            'discount_value': order.discount_value,
            'net_cost': order.net_cost,
            'subtotal_cost': order.subtotal_cost,
            'vat_cost': order.vat_cost,
            'total_cost': order.total_cost,
            'billing_company_name': order.billing_company_name,
            'billing_contact_name': order.billing_contact_name,
            'billing_email': order.billing_email,
            'billing_phone': order.billing_phone,
            'billing_address_1': order.billing_address_1,
            'billing_address_2': order.billing_address_2,
            'billing_address_town': order.billing_address_town,
            'billing_address_county': order.billing_address_county,
            'billing_address_postcode': order.billing_address_postcode,
            'billing_address_country': {
                'id': str(order.billing_address_country.pk),
                'name': order.billing_address_country.name,
            },
            'paid_on': None,
            'completed_on': None,
        }

    def test_get_draft_with_cancelled_quote(self):
        """Test getting an order in draft with a cancelled quote is allowed."""
        order = OrderWithCancelledQuoteFactory()

        url = reverse(
            'api-v3:omis-public:order:detail',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_404_with_invalid_public_token(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:omis-public:order:detail',
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
            'api-v3:omis-public:order:detail',
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
        order = OrderFactory(
            quote=QuoteFactory(),
            status=OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
        )

        url = reverse(
            'api-v3:omis-public:order:detail',
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
        order = OrderFactory(
            quote=QuoteFactory(),
            status=OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
        )

        url = reverse(
            'api-v3:omis-public:order:detail',
            kwargs={'public_token': order.public_token},
        )
        client = self.create_api_client(
            scope=scope,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
