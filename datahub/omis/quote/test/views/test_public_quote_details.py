import pytest
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import (
    OrderFactory,
)
from datahub.omis.order.test.factories import OrderWithOpenQuoteFactory
from datahub.omis.quote.models import TermsAndConditions
from datahub.omis.quote.test.factories import QuoteFactory


class TestPublicGetQuote(APITestMixin):
    """Get public quote test case."""

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        order = OrderFactory()

        url = reverse(
            'api-v3:public-omis:quote:detail',
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
            'api-v3:public-omis:quote:detail',
            kwargs={'public_token': order.public_token},
        )
        response = hawk_api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_whitelisted_ip(self, public_omis_api_client):
        """Test that making a request without the whitelisted client IP returns an error."""
        order = OrderFactory()

        url = reverse(
            'api-v3:public-omis:quote:detail',
            kwargs={'public_token': order.public_token},
        )
        public_omis_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = public_omis_api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('verb', ('post', 'patch', 'delete'))
    def test_verbs_not_allowed(self, verb, public_omis_api_client):
        """Test that makes sure the other verbs are not allowed."""
        order = OrderFactory(
            quote=QuoteFactory(),
            status=OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
        )

        url = reverse(
            'api-v3:public-omis:quote:detail',
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
        """Test a successful call to get a quote."""
        order = OrderFactory(
            quote=QuoteFactory(accepted_on=now()),
            status=order_status,
        )

        url = reverse(
            'api-v3:public-omis:quote:detail',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.get(url)

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

    def test_get_without_ts_and_cs(self, public_omis_api_client):
        """Test a successful call to get a quote without Ts and Cs."""
        order = OrderFactory(
            quote=QuoteFactory(accepted_on=now(), terms_and_conditions=None),
            status=OrderStatus.QUOTE_ACCEPTED,
        )

        url = reverse(
            'api-v3:public-omis:quote:detail',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['terms_and_conditions'] == ''

    def test_get_draft_with_cancelled_quote(self, public_omis_api_client):
        """Test getting a cancelled quote with order in draft is allowed."""
        order = OrderFactory(
            quote=QuoteFactory(cancelled_on=now()),
            status=OrderStatus.DRAFT,
        )

        url = reverse(
            'api-v3:public-omis:quote:detail',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.get(url)

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

    def test_404_if_order_doesnt_exist(self, public_omis_api_client):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:public-omis:quote:detail',
            kwargs={'public_token': ('1234-abcd-' * 5)},  # len(token) == 50
        )
        response = public_omis_api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_quote_doesnt_exist(self, public_omis_api_client):
        """Test that if the quote doesn't exist, the endpoint returns 404."""
        order = OrderFactory(status=OrderStatus.QUOTE_AWAITING_ACCEPTANCE)
        assert not order.quote

        url = reverse(
            'api-v3:public-omis:quote:detail',
            kwargs={'public_token': order.public_token},
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
            'api-v3:public-omis:quote:detail',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAcceptOrder(APITestMixin):
    """Tests for accepting a quote."""

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        order = OrderFactory()

        url = reverse(
            'api-v3:public-omis:quote:accept',
            kwargs={'public_token': order.public_token},
        )
        response = api_client.post(url, json_={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        order = OrderFactory()

        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        url = reverse(
            'api-v3:public-omis:quote:accept',
            kwargs={'public_token': order.public_token},
        )
        response = hawk_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_whitelisted_ip(self, public_omis_api_client):
        """Test that making a request without the whitelisted client IP returns an error."""
        order = OrderFactory()

        url = reverse(
            'api-v3:public-omis:quote:accept',
            kwargs={'public_token': order.public_token},
        )
        public_omis_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = public_omis_api_client.post(url, json_={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_404_if_order_doesnt_exist(self, public_omis_api_client):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:public-omis:quote:accept',
            kwargs={'public_token': ('1234-abcd-' * 5)},  # len(token) == 50
        )
        response = public_omis_api_client.post(url, json_={})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'disallowed_status,quote_fields',
        (
            (OrderStatus.DRAFT, {'cancelled_on': now()}),
            (OrderStatus.QUOTE_ACCEPTED, {}),
            (OrderStatus.PAID, {}),
            (OrderStatus.COMPLETE, {}),
        ),
    )
    def test_409_if_order_in_disallowed_status(
        self,
        disallowed_status,
        quote_fields,
        public_omis_api_client,
    ):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        quote = QuoteFactory(**quote_fields)
        order = OrderFactory(
            status=disallowed_status,
            quote=quote,
        )

        url = reverse(
            'api-v3:public-omis:quote:accept',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.post(url, json_={})

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                'The action cannot be performed '
                f'in the current status {disallowed_status.label}.'
            ),
        }

    def test_accept(self, public_omis_api_client):
        """Test that a quote can get accepted."""
        order = OrderWithOpenQuoteFactory()
        quote = order.quote

        url = reverse(
            'api-v3:public-omis:quote:accept',
            kwargs={'public_token': order.public_token},
        )

        with freeze_time('2017-07-12 13:00'):
            response = public_omis_api_client.post(url, json_={})

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
