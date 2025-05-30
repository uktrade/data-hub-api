import factory
import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import OrderFactory, OrderWithAcceptedQuoteFactory
from datahub.omis.payment.constants import PaymentGatewaySessionStatus
from datahub.omis.payment.govukpay import govuk_url
from datahub.omis.payment.models import Payment, PaymentGatewaySession
from datahub.omis.payment.test.factories import PaymentGatewaySessionFactory


class TestPublicCreatePaymentGatewaySession(APITestMixin):
    """Public create payment gateway session test case."""

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        order = OrderFactory()

        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
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
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        response = hawk_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_allowlisted_ip(self, public_omis_api_client):
        """Test that making a request without the allowlisted client IP returns an error."""
        order = OrderFactory()

        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        public_omis_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = public_omis_api_client.post(url, json_={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'verb_kwargs',
        [
            ('get', {}),
            ('patch', {'json_': {}}),
            ('delete', {'json_': {}}),
        ],
    )
    def test_verbs_not_allowed(self, verb_kwargs, public_omis_api_client):
        """Test that makes sure the other verbs are not allowed."""
        order = OrderWithAcceptedQuoteFactory()
        verb, kwargs = verb_kwargs
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        response = getattr(public_omis_api_client, verb)(url, **kwargs)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.fixture(autouse=True)
    def disable_payment_throttle_rate(self, monkeypatch):
        """Disable the throttling for all the tests in this class."""
        monkeypatch.setitem(
            settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'],
            'payment_gateway_session.create',
            None,
        )

    def test_create_first_session(self, requests_mock, public_omis_api_client):
        """Test a successful call to create a payment gateway session.

        This starts a GOV.UK payment and creates an OMIS payment gateway session
        object tracking it.
        """
        # mock GOV.UK response
        govuk_payment_id = '123abc123abc123abc123abc12'
        next_url = 'https://payment.example.com/123abc'
        json_response = {
            'state': {'status': 'created', 'finished': False},
            'payment_id': govuk_payment_id,
            '_links': {
                'next_url': {
                    'href': next_url,
                    'method': 'GET',
                },
            },
        }
        requests_mock.post(
            govuk_url('payments'),  # create payment
            status_code=201,
            json=json_response,
        )
        requests_mock.get(
            govuk_url(f'payments/{govuk_payment_id}'),  # get payment
            status_code=200,
            json=json_response,
        )

        assert PaymentGatewaySession.objects.count() == 0

        # make API call
        order = OrderWithAcceptedQuoteFactory()
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_201_CREATED

        # check payment gateway session record created
        assert PaymentGatewaySession.objects.count() == 1
        session = PaymentGatewaySession.objects.first()
        assert session.govuk_payment_id == govuk_payment_id
        assert session.status == PaymentGatewaySessionStatus.CREATED

        # check API response
        assert response.json() == {
            'id': str(session.id),
            'created_on': format_date_or_datetime(session.created_on),
            'status': PaymentGatewaySessionStatus.CREATED,
            'payment_url': next_url,
        }

    def test_create_cancels_other_ongoing_sessions(self, requests_mock, public_omis_api_client):
        """Test that creating a new payment gateway session cancels
        the other ongoing sessions and GOV.UK payments.

        Given:
            - ongoing session 1
            - ongoing session 2
            - failed session 3

        Calling this endpoint should:
            - cancel GOV.UK payment related to session 1
            - update the payment gateway session 1 status to 'cancelled'

            - cancel GOV.UK payment related to session 2
            - update the payment gateway session 2 status to 'cancelled'

            - start a new GOV.UK payment
            - create a payment gateway session related to it
        """
        order = OrderWithAcceptedQuoteFactory()
        existing_data = PaymentGatewaySessionFactory.create_batch(
            3,
            order=order,
            status=factory.Iterator(
                [
                    PaymentGatewaySessionStatus.CREATED,
                    PaymentGatewaySessionStatus.STARTED,
                    PaymentGatewaySessionStatus.FAILED,
                ],
            ),
        )

        # mock GOV.UK requests used to:
        # - refresh the payment gateway sessions
        # - cancel the GOV.UK payments
        # - refresh the payment gateway sessions again after the cancellation
        for session in existing_data:
            requests_mock.get(
                govuk_url(f'payments/{session.govuk_payment_id}'),
                [
                    # this is for the initial refresh
                    {
                        'status_code': 200,
                        'json': {'state': {'status': session.status}},
                    },
                    # this is for the second refresh after cancelling
                    {
                        'status_code': 200,
                        'json': {'state': {'status': 'cancelled'}},
                    },
                ],
            )
            requests_mock.post(
                govuk_url(f'payments/{session.govuk_payment_id}/cancel'),
                status_code=204,
            )

        # mock GOV.UK call used to create a new payment session
        govuk_payment_id = '123abc123abc123abc123abc12'
        next_url = 'https://payment.example.com/123abc'
        json_response = {
            'state': {'status': 'created', 'finished': False},
            'payment_id': govuk_payment_id,
            '_links': {
                'next_url': {
                    'href': next_url,
                    'method': 'GET',
                },
            },
        }
        requests_mock.post(
            govuk_url('payments'),  # create payment
            status_code=201,
            json=json_response,
        )
        requests_mock.get(
            govuk_url(f'payments/{govuk_payment_id}'),  # get payment
            status_code=200,
            json=json_response,
        )

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_201_CREATED

        # check sessions cancelled
        for existing_session in existing_data[:-1]:
            existing_session.refresh_from_db()
            assert existing_session.status == PaymentGatewaySessionStatus.CANCELLED

        # check session record created
        assert PaymentGatewaySession.objects.ongoing().count() == 1
        session = PaymentGatewaySession.objects.ongoing().first()
        assert session.govuk_payment_id == govuk_payment_id

        # check API response
        assert response.json() == {
            'id': str(session.id),
            'created_on': format_date_or_datetime(session.created_on),
            'status': PaymentGatewaySessionStatus.CREATED,
            'payment_url': next_url,
        }

    @pytest.mark.parametrize('govuk_status_code', [400, 401, 404, 409, 500])
    def test_500_if_govuk_pay_errors_when_cancelling(
        self,
        govuk_status_code,
        requests_mock,
        public_omis_api_client,
    ):
        """Test that if GOV.UK Pay errors whilst cancelling some other ongoing
        sessions/payments, the endpoint returns 500 to keep the system consistent.

        Possible GOV.UK errors when cancelling:
        - 400 - BAD REQUEST
        - 401 - UNAUTHORIZED
        - 404 - NOT FOUND
        - 409 - CONFLICT
        - 500 - INTERNAL SERVER ERROR

        In all these cases we return 500 as all those GOV.UK errors are unexpected.
        """
        order = OrderWithAcceptedQuoteFactory()
        existing_session = PaymentGatewaySessionFactory(
            order=order,
            status=PaymentGatewaySessionStatus.CREATED,
        )

        # mock GOV.UK requests used to
        # - refresh the existing payment gateway session
        # - cancel the GOV.UK payment
        requests_mock.get(
            govuk_url(f'payments/{existing_session.govuk_payment_id}'),
            status_code=200,
            json={
                'state': {'status': existing_session.status},
            },
        )
        requests_mock.post(
            govuk_url(f'payments/{existing_session.govuk_payment_id}/cancel'),
            status_code=govuk_status_code,
        )

        # make API call
        assert PaymentGatewaySession.objects.count() == 1

        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # check no session created
        assert PaymentGatewaySession.objects.count() == 1

    @pytest.mark.parametrize('govuk_status_code', [400, 401, 422, 500])
    def test_500_if_govuk_pay_errors_when_creating(
        self,
        govuk_status_code,
        requests_mock,
        public_omis_api_client,
    ):
        """Test that if GOV.UK Pay errors whilst creating a new payment, the endpoint returns 500.

        Possible GOV.UK errors:
        - 400 - BAD REQUEST
        - 401 - UNAUTHORIZED
        - 422 - UNPROCESSABLE ENTITY
        - 500 - INTERNAL SERVER ERROR

        In all these cases we return 500 as all those GOV.UK errors are unexpected.
        """
        # mock GOV.UK response
        requests_mock.post(
            govuk_url('payments'),
            status_code=govuk_status_code,
        )

        assert PaymentGatewaySession.objects.count() == 0

        # make API call
        order = OrderWithAcceptedQuoteFactory()
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # check no session created
        assert PaymentGatewaySession.objects.count() == 0

    @pytest.mark.parametrize(
        'disallowed_status',
        [
            OrderStatus.PAID,
            OrderStatus.COMPLETE,
        ],
    )
    def test_409_if_order_in_disallowed_status(self, disallowed_status, public_omis_api_client):
        """Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        assert PaymentGatewaySession.objects.count() == 0

        order = OrderFactory(status=disallowed_status)
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                f'The action cannot be performed in the current status {disallowed_status.label}.'
            ),
        }

        # check no session created
        assert PaymentGatewaySession.objects.count() == 0

    def test_409_if_refresh_updates_order_status_to_paid(
        self,
        requests_mock,
        public_omis_api_client,
    ):
        """Test that if the system is not up-to-date, the order is in quote_accepted
        but the GOV.UK payment happens, the endpoint triggers a check on existing
        sessions, realises that one finished successfully and records the payment
        marking the order as 'paid'.
        For this reason, the endpoint returns 409 - Conflict as no other payment
        can be made.
        """
        # set up db
        order = OrderWithAcceptedQuoteFactory()
        existing_session = PaymentGatewaySessionFactory(
            order=order,
            status=PaymentGatewaySessionStatus.STARTED,
        )

        # mock GOV.UK requests used to refresh the payment session.
        # GOV.UK Pay says that the payment completed successfully
        requests_mock.get(
            govuk_url(f'payments/{existing_session.govuk_payment_id}'),
            status_code=200,
            json={
                'amount': order.total_cost,
                'state': {'status': 'success'},
                'email': 'email@example.com',
                'reference': '12345',
                'created_date': '2018-02-13T14:56:56.734Z',
                'card_details': {
                    'last_digits_card_number': '1111',
                    'cardholder_name': 'John Doe',
                    'expiry_date': '01/20',
                    'billing_address': {
                        'line1': 'line 1 address',
                        'line2': 'line 2 address',
                        'postcode': 'SW1A 1AA',
                        'city': 'London',
                        'country': 'GB',
                    },
                    'card_brand': 'Visa',
                },
            },
        )

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )
        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_409_CONFLICT

        # check session record
        existing_session.refresh_from_db()
        assert existing_session.status == PaymentGatewaySessionStatus.SUCCESS

        # check order and pyament
        order.refresh_from_db()
        assert order.status == OrderStatus.PAID

        assert Payment.objects.filter(order=order).count() == 1

    @pytest.mark.parametrize(
        'order_status',
        [
            OrderStatus.DRAFT,
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.CANCELLED,
        ],
    )
    def test_404_if_order_not_accessible(self, order_status, public_omis_api_client):
        """Test that if the order is not publicly accessible, the endpoint returns 404."""
        order = OrderFactory(status=order_status)

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )

        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_order_doesnt_exist(self, public_omis_api_client):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': ('1234-abcd-' * 5)},
        )
        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @freeze_time('2018-03-01 00:00:00')
    def test_429_if_too_many_requests_made(
        self,
        local_memory_cache,
        requests_mock,
        monkeypatch,
        public_omis_api_client,
    ):
        """Test that the throttling for the create endpoint works if its rate is set."""
        monkeypatch.setitem(
            settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'],
            'payment_gateway_session.create',
            '3/sec',
        )

        # mock GOV.UK response
        govuk_payment_id = '123abc123abc123abc123abc12'
        json_response = {
            'state': {'status': 'created', 'finished': False},
            'payment_id': govuk_payment_id,
            '_links': {
                'next_url': {
                    'href': 'https://payment.example.com/123abc',
                    'method': 'GET',
                },
            },
        }
        requests_mock.post(
            govuk_url('payments'),  # create payment
            status_code=201,
            json=json_response,
        )
        requests_mock.get(
            govuk_url(f'payments/{govuk_payment_id}'),  # get payment
            status_code=200,
            json=json_response,
        )
        requests_mock.post(
            govuk_url(f'payments/{govuk_payment_id}/cancel'),  # cancel payment
            status_code=204,
        )

        order = OrderWithAcceptedQuoteFactory()

        url = reverse(
            'api-v3:public-omis:payment-gateway-session:collection',
            kwargs={'public_token': order.public_token},
        )

        # the 4th time it should error
        for _ in range(3):
            response = public_omis_api_client.post(url, json_={})
            assert response.status_code == status.HTTP_201_CREATED

        response = public_omis_api_client.post(url, json_={})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestPublicGetPaymentGatewaySession(APITestMixin):
    """Public get payment gateway session test case."""

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        order = OrderFactory()
        session = PaymentGatewaySessionFactory(
            order=order,
            status=PaymentGatewaySessionStatus.CREATED,
        )

        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': order.public_token, 'pk': session.pk},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        order = OrderFactory()
        session = PaymentGatewaySessionFactory(
            order=order,
            status=PaymentGatewaySessionStatus.CREATED,
        )

        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': order.public_token, 'pk': session.pk},
        )
        response = hawk_api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_allowlisted_ip(self, public_omis_api_client):
        """Test that making a request without the allowlisted client IP returns an error."""
        order = OrderFactory()
        session = PaymentGatewaySessionFactory(
            order=order,
            status=PaymentGatewaySessionStatus.CREATED,
        )

        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': order.public_token, 'pk': session.pk},
        )
        public_omis_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = public_omis_api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('verb', ['post', 'patch', 'delete'])
    def test_verbs_not_allowed(self, verb, public_omis_api_client):
        """Test that makes sure the other verbs are not allowed."""
        order = OrderWithAcceptedQuoteFactory()
        session = PaymentGatewaySessionFactory(order=order)

        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': order.public_token, 'pk': session.id},
        )
        response = getattr(public_omis_api_client, verb)(url, json_={})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'order_status',
        [
            OrderStatus.QUOTE_ACCEPTED,
            OrderStatus.PAID,
            OrderStatus.COMPLETE,
        ],
    )
    @pytest.mark.parametrize(
        'session_status',
        [
            PaymentGatewaySessionStatus.CREATED,
            PaymentGatewaySessionStatus.STARTED,
            PaymentGatewaySessionStatus.SUBMITTED,
        ],
    )
    def test_get(self, order_status, session_status, requests_mock, public_omis_api_client):
        """Test a successful call to get a payment gateway session."""
        order = OrderFactory(status=order_status)
        session = PaymentGatewaySessionFactory(
            order=order,
            status=session_status,
        )

        # mock GOV.UK Pay request used to get the existing session
        next_url = 'https://payment.example.com/123abc'
        requests_mock.get(
            govuk_url(f'payments/{session.govuk_payment_id}'),
            status_code=200,
            json={
                'state': {'status': session.status},
                'payment_id': session.govuk_payment_id,
                '_links': {
                    'next_url': {
                        'href': next_url,
                        'method': 'GET',
                    },
                },
            },
        )

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': order.public_token, 'pk': session.id},
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # check API response
        assert response.json() == {
            'id': str(session.id),
            'created_on': format_date_or_datetime(session.created_on),
            'status': session.status,
            'payment_url': next_url,
        }

    @pytest.mark.parametrize(
        'session_status',
        [
            PaymentGatewaySessionStatus.SUCCESS,
            PaymentGatewaySessionStatus.FAILED,
            PaymentGatewaySessionStatus.CANCELLED,
            PaymentGatewaySessionStatus.ERROR,
        ],
    )
    def test_doesnt_call_govuk_pay_if_session_finished(
        self,
        session_status,
        requests_mock,
        public_omis_api_client,
    ):
        """Test a successful call to get a payment gateway session when the session is finished.
        The system does not call GOV.UK Pay as the record is up-to-date.
        """
        session = PaymentGatewaySessionFactory(status=session_status)

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': session.order.public_token, 'pk': session.id},
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # check API response
        assert response.json() == {
            'id': str(session.id),
            'created_on': format_date_or_datetime(session.created_on),
            'status': session.status,
            'payment_url': '',
        }
        assert not requests_mock.called

    @pytest.mark.parametrize(
        ('govuk_status', 'payment_url'),
        [
            (PaymentGatewaySessionStatus.CREATED, 'https://payment.example.com/123abc'),
            (PaymentGatewaySessionStatus.STARTED, 'https://payment.example.com/123abc'),
            (PaymentGatewaySessionStatus.SUBMITTED, 'https://payment.example.com/123abc'),
            (PaymentGatewaySessionStatus.FAILED, ''),
            (PaymentGatewaySessionStatus.CANCELLED, ''),
            (PaymentGatewaySessionStatus.ERROR, ''),
        ],
    )
    def test_with_different_govuk_payment_status_updates_session(
        self,
        govuk_status,
        payment_url,
        requests_mock,
        public_omis_api_client,
    ):
        """Test that if the GOV.UK payment status is not the same as the payment gateway session one,
        the record is updated.
        """
        # choose an initial status != from the govuk one to test the update
        initial_status = PaymentGatewaySessionStatus.CREATED
        if initial_status == govuk_status:
            initial_status = PaymentGatewaySessionStatus.STARTED

        session = PaymentGatewaySessionFactory(status=initial_status)

        # mock GOV.UK call used to get the existing session
        requests_mock.get(
            govuk_url(f'payments/{session.govuk_payment_id}'),
            status_code=200,
            json={
                'state': {'status': govuk_status},
                'payment_id': session.govuk_payment_id,
                '_links': {
                    'next_url': None if not payment_url else {'href': payment_url},
                },
            },
        )

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': session.order.public_token, 'pk': session.id},
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # refresh record
        session.refresh_from_db()
        assert session.status == govuk_status

        # check API response
        assert response.json() == {
            'id': str(session.id),
            'created_on': format_date_or_datetime(session.created_on),
            'status': govuk_status,
            'payment_url': payment_url,
        }

    def test_with_govuk_payment_success_updates_order(self, requests_mock, public_omis_api_client):
        """Test that if the GOV.UK payment status is `success` and the payment gateway session is
        out of date, the record is updated, the related order marked as `paid` and an OMIS
        `payment.Payment` record created from the GOV.UK response data one.
        """
        order = OrderWithAcceptedQuoteFactory()
        session = PaymentGatewaySessionFactory(
            order=order,
            status=PaymentGatewaySessionStatus.CREATED,
        )

        # mock GOV.UK calls used to refresh the payment session
        # Pay says that the payment completed successfully
        requests_mock.get(
            govuk_url(f'payments/{session.govuk_payment_id}'),
            status_code=200,
            json={
                'amount': order.total_cost,
                'state': {'status': 'success'},
                'email': 'email@example.com',
                'reference': '12345',
                'created_date': '2018-02-13T14:56:56.734Z',
                '_links': {
                    'next_url': None,
                },
                'card_details': {
                    'last_digits_card_number': '1111',
                    'cardholder_name': 'John Doe',
                    'expiry_date': '01/20',
                    'billing_address': {
                        'line1': 'line 1 address',
                        'line2': 'line 2 address',
                        'postcode': 'SW1A 1AA',
                        'city': 'London',
                        'country': 'GB',
                    },
                    'card_brand': 'Visa',
                },
            },
        )

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': order.public_token, 'pk': session.id},
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # check API response
        assert response.json() == {
            'id': str(session.id),
            'created_on': format_date_or_datetime(session.created_on),
            'status': PaymentGatewaySessionStatus.SUCCESS,
            'payment_url': '',
        }

        # check session record
        session.refresh_from_db()
        assert session.status == PaymentGatewaySessionStatus.SUCCESS

        # check order and payment
        order.refresh_from_db()
        assert order.status == OrderStatus.PAID
        assert Payment.objects.filter(order=order).count() == 1

    @pytest.mark.parametrize('govuk_status_code', [401, 404, 500])
    def test_500_if_govuk_pay_errors(
        self,
        govuk_status_code,
        requests_mock,
        public_omis_api_client,
    ):
        """Test that if GOV.UK Pay errors whilst getting a payment, the endpoint returns 500.

        Possible GOV.UK errors:
        - 401 - UNAUTHORIZED
        - 404 - NOT FOUND
        - 500 - INTERNAL SERVER ERROR
        """
        order = OrderWithAcceptedQuoteFactory()
        session = PaymentGatewaySessionFactory(
            order=order,
            status=PaymentGatewaySessionStatus.CREATED,
        )

        requests_mock.get(
            govuk_url(f'payments/{session.govuk_payment_id}'),
            status_code=govuk_status_code,
        )

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': order.public_token, 'pk': session.id},
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.parametrize(
        'order_status',
        [
            OrderStatus.DRAFT,
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.CANCELLED,
        ],
    )
    def test_404_if_in_disallowed_status(self, order_status, public_omis_api_client):
        """Test that if the order is not in an allowed state, the endpoint returns 404."""
        order = OrderFactory(status=order_status)
        session = PaymentGatewaySessionFactory(order=order)

        # make API call
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={'public_token': order.public_token, 'pk': session.id},
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_order_doesnt_exist(self, public_omis_api_client):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={
                'public_token': ('1234-abcd-' * 5),
                'pk': '00000000-0000-0000-0000-000000000000',
            },
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_session_doesnt_exist(self, public_omis_api_client):
        """Test that if the payment gateway session doesn't exist, the endpoint returns 404."""
        order = OrderWithAcceptedQuoteFactory()
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={
                'public_token': order.public_token,
                'pk': '00000000-0000-0000-0000-000000000000',
            },
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_session_belongs_to_another_order(self, public_omis_api_client):
        """Test that if the payment gateway session belongs to another order,
        the endpoint returns 404.
        """
        orders = OrderWithAcceptedQuoteFactory.create_batch(2)
        sessions = PaymentGatewaySessionFactory.create_batch(2, order=factory.Iterator(orders))
        url = reverse(
            'api-v3:public-omis:payment-gateway-session:detail',
            kwargs={
                'public_token': orders[0].public_token,
                'pk': sessions[1].id,
            },
        )
        response = public_omis_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
