import uuid
from unittest import mock

import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import (
    OrderFactory,
    OrderWithCancelledQuoteFactory,
    OrderWithOpenQuoteFactory,
)
from datahub.omis.quote.models import Quote, TermsAndConditions
from datahub.omis.quote.test.factories import QuoteFactory


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestCreatePreviewOrder(APITestMixin):
    """Tests for creating and previewing a quote."""

    @pytest.mark.parametrize('quote_view_name', ('detail', 'preview'))
    def test_404_if_order_doesnt_exist(self, quote_view_name):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            f'api-v3:omis:quote:{quote_view_name}',
            kwargs={'order_pk': uuid.uuid4()},
        )
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('quote_view_name', ('detail', 'preview'))
    def test_409_if_theres_already_a_valid_quote(self, quote_view_name):
        """Test that if the order has already an active quote, the endpoint returns 409."""
        order = OrderWithOpenQuoteFactory()

        url = reverse(
            f'api-v3:omis:quote:{quote_view_name}',
            kwargs={'order_pk': order.pk},
        )
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {'detail': "There's already an active quote."}

    @pytest.mark.parametrize('quote_view_name', ('detail', 'preview'))
    @pytest.mark.parametrize(
        'disallowed_status', (
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
            OrderStatus.PAID,
            OrderStatus.COMPLETE,
            OrderStatus.CANCELLED,
        ),
    )
    def test_409_if_order_in_disallowed_status(self, quote_view_name, disallowed_status):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        order = OrderFactory(status=disallowed_status)

        url = reverse(
            f'api-v3:omis:quote:{quote_view_name}',
            kwargs={'order_pk': order.pk},
        )
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                'The action cannot be performed '
                f'in the current status {disallowed_status.label}.'
            ),
        }

    @pytest.mark.parametrize('quote_view_name', ('detail', 'preview'))
    @pytest.mark.parametrize(
        'field,value',
        (
            ('service_types', []),
            ('description', ''),
            ('delivery_date', None),
        ),
    )
    @freeze_time('2017-04-18 13:00:00.000000')
    def test_400_if_incomplete_order(self, quote_view_name, field, value):
        """If the order is incomplete, the quote cannot be generated."""
        order = OrderFactory(**{field: value})

        url = reverse(
            f'api-v3:omis:quote:{quote_view_name}',
            kwargs={'order_pk': order.pk},
        )
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            field: ['This field is required.'],
        }

    @pytest.mark.parametrize('quote_view_name', ('detail', 'preview'))
    @freeze_time('2017-04-18 13:00:00.000000')
    def test_400_if_expiry_date_passed(self, quote_view_name):
        """
        If the generated quote expiry date is in the past because the delivery date
        is too close, return 400.
        """
        order = OrderFactory(
            delivery_date=dateutil_parse('2017-04-20').date(),
        )

        url = reverse(
            f'api-v3:omis:quote:{quote_view_name}',
            kwargs={'order_pk': order.pk},
        )
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'delivery_date': [
                'The calculated expiry date for the quote is in the past. '
                'You might be able to fix this by changing the delivery date.',
            ],
        }

    @freeze_time('2017-04-18 13:00:00.000000')
    @pytest.mark.parametrize(
        'order_factory',
        (OrderFactory, OrderWithCancelledQuoteFactory),
    )
    def test_create_success(self, order_factory):
        """Test a successful call to create a quote."""
        order = order_factory(
            delivery_date=dateutil_parse('2017-06-18').date(),
        )
        orig_quote = order.quote

        url = reverse('api-v3:omis:quote:detail', kwargs={'order_pk': order.pk})
        response = self.api_client.post(url)

        order.refresh_from_db()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'content': order.quote.content,
            'terms_and_conditions': TermsAndConditions.objects.first().content,
            'created_on': '2017-04-18T13:00:00Z',
            'created_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'cancelled_on': None,
            'cancelled_by': None,
            'accepted_on': None,
            'accepted_by': None,
            'expires_on': '2017-05-18',  # now + 30 days
        }

        assert order.quote
        assert order.quote != orig_quote

    def test_create_as_atomic_operation(self):
        """
        Test that if there's a problem when saving the order, the quote is not saved
        either so that we keep db integrity.
        """
        order = OrderFactory()

        url = reverse('api-v3:omis:quote:detail', kwargs={'order_pk': order.pk})

        with mock.patch.object(Order, 'save') as mocked_save:
            mocked_save.side_effect = Exception()

            with pytest.raises(Exception):
                self.api_client.post(url)

        order.refresh_from_db()
        assert not order.quote
        assert not Quote.objects.count()

    @freeze_time('2017-04-18 13:00:00.000000')
    @pytest.mark.parametrize(
        'order_factory',
        (OrderFactory, OrderWithCancelledQuoteFactory),
    )
    def test_preview_success(self, order_factory):
        """
        Test a successful call to preview a quote.
        Changes are not saved in the db.
        """
        order = order_factory(
            delivery_date=dateutil_parse('2017-06-18').date(),
        )
        orig_quote = order.quote

        url = reverse('api-v3:omis:quote:preview', kwargs={'order_pk': order.pk})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert order.reference in response.json()['content']
        assert response.json() == {
            'content': response.json()['content'],
            'terms_and_conditions': TermsAndConditions.objects.first().content,
            'created_on': None,
            'created_by': None,
            'cancelled_on': None,
            'cancelled_by': None,
            'accepted_on': None,
            'accepted_by': None,
            'expires_on': '2017-05-18',  # now + 30 days
        }

        order.refresh_from_db()
        assert order.quote == orig_quote


class TestGetQuote(APITestMixin):
    """Get quote test case."""

    def test_get(self):
        """Test a successful call to get a quote."""
        order = OrderWithOpenQuoteFactory()
        quote = order.quote

        url = reverse('api-v3:omis:quote:detail', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'created_on': format_date_or_datetime(quote.created_on),
            'created_by': {
                'id': str(quote.created_by.pk),
                'first_name': quote.created_by.first_name,
                'last_name': quote.created_by.last_name,
                'name': quote.created_by.name,
            },
            'cancelled_on': None,
            'cancelled_by': None,
            'accepted_on': None,
            'accepted_by': None,
            'expires_on': quote.expires_on.isoformat(),
            'content': quote.content,
            'terms_and_conditions': TermsAndConditions.objects.first().content,
        }

    def test_get_without_ts_and_cs(self):
        """Test a successful call to get a quote without Ts and Cs."""
        order = OrderFactory(
            quote=QuoteFactory(terms_and_conditions=None),
            status=OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
        )

        url = reverse('api-v3:omis:quote:detail', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['terms_and_conditions'] == ''

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse('api-v3:omis:quote:detail', kwargs={'order_pk': uuid.uuid4()})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_quote_doesnt_exist(self):
        """Test that if the quote doesn't exist, the endpoint returns 404."""
        order = OrderFactory()
        assert not order.quote

        url = reverse('api-v3:omis:quote:detail', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCancelOrder(APITestMixin):
    """Tests for cancelling a quote."""

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            f'api-v3:omis:quote:cancel',
            kwargs={'order_pk': uuid.uuid4()},
        )
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'disallowed_status', (
            OrderStatus.PAID,
            OrderStatus.COMPLETE,
            OrderStatus.CANCELLED,
        ),
    )
    def test_409_if_order_in_disallowed_status(self, disallowed_status):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        quote = QuoteFactory()
        order = OrderFactory(
            status=disallowed_status,
            quote=quote,
        )

        url = reverse(
            f'api-v3:omis:quote:cancel',
            kwargs={'order_pk': order.pk},
        )
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                'The action cannot be performed '
                f'in the current status {disallowed_status.label}.'
            ),
        }

    def test_without_quote(self):
        """Test that if the order doesn't have any quote, the endpoint returns 404."""
        order = OrderFactory()

        url = reverse(
            f'api-v3:omis:quote:cancel',
            kwargs={'order_pk': order.pk},
        )
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_with_open_quote(self):
        """Test that if the quote is open, it gets cancelled."""
        order = OrderWithOpenQuoteFactory()
        quote = order.quote

        url = reverse(
            f'api-v3:omis:quote:cancel',
            kwargs={'order_pk': order.pk},
        )
        with freeze_time('2017-07-12 13:00') as mocked_now:
            response = self.api_client.post(url)

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {
                'created_on': format_date_or_datetime(quote.created_on),
                'created_by': {
                    'id': str(quote.created_by.pk),
                    'first_name': quote.created_by.first_name,
                    'last_name': quote.created_by.last_name,
                    'name': quote.created_by.name,
                },
                'cancelled_on': format_date_or_datetime(mocked_now()),
                'cancelled_by': {
                    'id': str(self.user.pk),
                    'first_name': self.user.first_name,
                    'last_name': self.user.last_name,
                    'name': self.user.name,
                },
                'accepted_on': None,
                'accepted_by': None,
                'expires_on': quote.expires_on.isoformat(),
                'content': quote.content,
                'terms_and_conditions': TermsAndConditions.objects.first().content,
            }

            quote.refresh_from_db()
            assert quote.is_cancelled()
