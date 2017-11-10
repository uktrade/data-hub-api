import pytest

from django.utils.timezone import now
from freezegun import freeze_time
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.oauth.scopes import Scope
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import OrderFactory, OrderWithOpenQuoteFactory

from ..factories import QuoteFactory
from ...models import TermsAndConditions


class TestPublicGetQuote(APITestMixin):
    """Get public quote test case."""

    @pytest.mark.parametrize(
        'order_status',
        (
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
            OrderStatus.paid,
            OrderStatus.complete
        )
    )
    def test_get(self, order_status):
        """Test a successful call to get a quote."""
        order = OrderFactory(
            quote=QuoteFactory(accepted_on=now()),
            status=order_status
        )

        url = reverse(
            'api-v3:omis-public:quote:detail',
            kwargs={'public_token': order.public_token}
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.get(url, format='json')

        quote = order.quote
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'created_on': format_date_or_datetime(quote.created_on),
            'cancelled_on': None,
            'accepted_on': format_date_or_datetime(quote.accepted_on),
            'expires_on': quote.expires_on.isoformat(),
            'content': quote.content,
            'terms_and_conditions': TermsAndConditions.objects.first().content,
        }

    def test_get_without_ts_and_cs(self):
        """Test a successful call to get a quote without Ts and Cs."""
        order = OrderFactory(
            quote=QuoteFactory(accepted_on=now(), terms_and_conditions=None),
            status=OrderStatus.quote_accepted
        )

        url = reverse(
            'api-v3:omis-public:quote:detail',
            kwargs={'public_token': order.public_token}
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['terms_and_conditions'] == ''

    def test_get_draft_with_cancelled_quote(self):
        """Test getting a cancelled quote with order in draft is allowed."""
        order = OrderFactory(
            quote=QuoteFactory(cancelled_on=now()),
            status=OrderStatus.draft
        )

        url = reverse(
            'api-v3:omis-public:quote:detail',
            kwargs={'public_token': order.public_token}
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.get(url, format='json')

        quote = order.quote
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'created_on': format_date_or_datetime(quote.created_on),
            'cancelled_on': format_date_or_datetime(quote.cancelled_on),
            'accepted_on': None,
            'expires_on': quote.expires_on.isoformat(),
            'content': quote.content,
            'terms_and_conditions': TermsAndConditions.objects.first().content,
        }

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:omis-public:quote:detail',
            kwargs={'public_token': ('1234-abcd-' * 5)}  # len(token) == 50
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.get(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_quote_doesnt_exist(self):
        """Test that if the quote doesn't exist, the endpoint returns 404."""
        order = OrderFactory(status=OrderStatus.quote_awaiting_acceptance)
        assert not order.quote

        url = reverse(
            'api-v3:omis-public:quote:detail',
            kwargs={'public_token': order.public_token}
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.get(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'order_status',
        (OrderStatus.draft, OrderStatus.cancelled)
    )
    def test_404_if_in_disallowed_status(self, order_status):
        """Test that if the order is not in an allowed state, the endpoint returns 404."""
        order = OrderFactory(status=order_status)

        url = reverse(
            'api-v3:omis-public:order:detail',
            kwargs={'public_token': order.public_token}
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('verb', ('post', 'patch', 'delete'))
    def test_verbs_not_allowed(self, verb):
        """Test that makes sure the other verbs are not allowed."""
        order = OrderFactory(
            quote=QuoteFactory(),
            status=OrderStatus.quote_awaiting_acceptance
        )

        url = reverse(
            'api-v3:omis-public:quote:detail',
            kwargs={'public_token': order.public_token}
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = getattr(client, verb)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'scope',
        (s.value for s in Scope if s != Scope.public_omis_front_end.value)
    )
    def test_403_if_scope_not_allowed(self, scope):
        """Test that other oauth2 scopes are not allowed."""
        order = OrderFactory(
            quote=QuoteFactory(),
            status=OrderStatus.quote_awaiting_acceptance
        )

        url = reverse(
            'api-v3:omis-public:quote:detail',
            kwargs={'public_token': order.public_token}
        )
        client = self.create_api_client(
            scope=scope,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAcceptOrder(APITestMixin):
    """Tests for accepting a quote."""

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:omis-public:quote:accept',
            kwargs={'public_token': ('1234-abcd-' * 5)}  # len(token) == 50
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.post(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'disallowed_status,quote_fields',
        (
            (OrderStatus.draft, {'cancelled_on': now()}),
            (OrderStatus.quote_accepted, {}),
            (OrderStatus.paid, {}),
            (OrderStatus.complete, {}),
        )
    )
    def test_409_if_order_in_disallowed_status(self, disallowed_status, quote_fields):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        quote = QuoteFactory(**quote_fields)
        order = OrderFactory(
            status=disallowed_status,
            quote=quote
        )

        url = reverse(
            f'api-v3:omis-public:quote:accept',
            kwargs={'public_token': order.public_token}
        )
        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        response = client.post(url, format='json')

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                'The action cannot be performed '
                f'in the current status {OrderStatus[disallowed_status]}.'
            )
        }

    def test_accept(self):
        """Test that a quote can get accepted."""
        order = OrderWithOpenQuoteFactory()
        quote = order.quote

        url = reverse(
            f'api-v3:omis-public:quote:accept',
            kwargs={'public_token': order.public_token}
        )

        client = self.create_api_client(
            scope=Scope.public_omis_front_end,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        with freeze_time('2017-07-12 13:00'):
            response = client.post(url, format='json')

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {
                'created_on': format_date_or_datetime(quote.created_on),
                'accepted_on': format_date_or_datetime(now()),
                'cancelled_on': None,
                'expires_on': quote.expires_on.isoformat(),
                'content': quote.content,
                'terms_and_conditions': TermsAndConditions.objects.first().content,
            }

            quote.refresh_from_db()
            assert quote.is_accepted()
            assert quote.accepted_on == now()
