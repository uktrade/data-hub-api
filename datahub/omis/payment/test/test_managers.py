from unittest import mock

import factory
import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings

from datahub.company.test.factories import AdviserFactory
from datahub.core.exceptions import APIConflictException
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import (
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
)
from datahub.omis.payment.constants import PaymentGatewaySessionStatus, PaymentMethod
from datahub.omis.payment.govukpay import govuk_url, GOVUKPayAPIException
from datahub.omis.payment.models import Payment, PaymentGatewaySession
from datahub.omis.payment.test.factories import PaymentGatewaySessionFactory


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestPaymentManager:
    """Tests for the Payment Manager."""

    @mock.patch('datahub.omis.payment.managers.generate_datetime_based_reference')
    def test_create_from_order(
        self,
        mocked_generate_datetime_based_reference,
    ):
        """Test that Payment.objects.create_from_order creates a payment."""
        mocked_generate_datetime_based_reference.return_value = '201702010004'

        order = OrderPaidFactory()
        by = AdviserFactory()
        attrs = {
            'transaction_reference': 'lorem ipsum',
            'amount': 1001,
            'received_on': dateutil_parse('2017-01-01').date(),
        }
        payment = Payment.objects.create_from_order(
            order=order, by=by, attrs=attrs,
        )

        payment.refresh_from_db()
        assert payment.reference == '201702010004'
        assert payment.created_by == by
        assert payment.order == order
        assert payment.transaction_reference == attrs['transaction_reference']
        assert payment.additional_reference == ''
        assert payment.amount == attrs['amount']
        assert payment.received_on == attrs['received_on']


class TestPaymentGatewaySessionManager:
    """Tests for the Payment Gateway Session Manager."""

    def test_create_first_session_from_order(self, requests_mock, monkeypatch):
        """
        Test the successful creation of the first payment gateway session for an order.
        """
        monkeypatch.setattr(
            'uuid.uuid4',
            mock.Mock(return_value='0123abcd-0000-0000-0000-000000000000'),
        )

        # mock request
        govuk_payment_id = '123abc123abc123abc123abc12'
        govuk_payments_url = govuk_url('payments')
        requests_mock.post(
            govuk_payments_url,
            status_code=201,
            json={
                'state': {'status': 'created', 'finished': False},
                'payment_id': govuk_payment_id,
                '_links': {
                    'next_url': {
                        'href': 'https://payment.example.com/123abc',
                        'method': 'GET',
                    },
                },
            },
        )

        assert PaymentGatewaySession.objects.count() == 0

        # call method
        adviser = AdviserFactory()
        order = OrderWithAcceptedQuoteFactory()
        session = PaymentGatewaySession.objects.create_from_order(
            order=order,
            attrs={'created_by': adviser},
        )

        # check session
        assert session.order == order
        assert session.status == PaymentGatewaySessionStatus.CREATED
        assert session.govuk_payment_id == govuk_payment_id
        assert session.created_by == adviser

        assert PaymentGatewaySession.objects.count() == 1

        # check mocked request
        assert requests_mock.call_count == 1
        assert requests_mock.request_history[-1].url == govuk_payments_url
        assert requests_mock.request_history[-1].json() == {
            'amount': order.total_cost,
            'reference': f'{order.reference}-0123ABCD',
            'description': settings.GOVUK_PAY_PAYMENT_DESCRIPTION.format(
                reference=order.reference,
            ),
            'return_url': settings.GOVUK_PAY_RETURN_URL.format(
                public_token=order.public_token,
                session_id=session.pk,
            ),
        }

    def test_create_cancels_other_sessions(self, requests_mock):
        """
        Test that creating a new payment gateway session cancels
        the other ongoing sessions and GOV.UK payments.

        Given:
            - ongoing session 1
            - ongoing session 2
            - failed session 3

        Calling .create_from_order should:
            - cancel the GOV.UK payment related to session 1
            - update the payment gateway session 1 status to 'cancelled'

            - cancel the GOV.UK payment related to session 2
            - update the payment gateway session 2 status to 'cancelled'

            - start a new GOV.UK payment
            - create a payment gateway session related to it
        """
        order = OrderWithAcceptedQuoteFactory()
        existing_data = PaymentGatewaySessionFactory.create_batch(
            3,
            order=order,
            status=factory.Iterator([
                PaymentGatewaySessionStatus.CREATED,
                PaymentGatewaySessionStatus.STARTED,
                PaymentGatewaySessionStatus.FAILED,
            ]),
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

        # mock GOV.UK request used to create a new payment session
        govuk_payment_id = '123abc123abc123abc123abc12'
        requests_mock.post(
            govuk_url('payments'),
            status_code=201,
            json={
                'state': {'status': 'created', 'finished': False},
                'payment_id': govuk_payment_id,
                '_links': {
                    'next_url': {
                        'href': 'https://payment.example.com/123abc',
                        'method': 'GET',
                    },
                },
            },
        )

        assert PaymentGatewaySession.objects.count() == 3

        session = PaymentGatewaySession.objects.create_from_order(order=order)

        # check sessions cancelled
        for existing_session in existing_data[:-1]:
            existing_session.refresh_from_db()
            assert existing_session.status == PaymentGatewaySessionStatus.CANCELLED

        assert PaymentGatewaySession.objects.count() == 4

        # check session record created
        session.refresh_from_db()
        assert session.govuk_payment_id == govuk_payment_id

        # check mocked requests:
        #   2 refresh / 2 cancel - 2 refresh / 1 create
        assert requests_mock.call_count == (2 + 2 + 2 + 1)
        assert requests_mock.request_history[-1].json() == {
            'amount': order.total_cost,
            'reference': f'{order.reference}-{str(session.id)[:8].upper()}',
            'description': settings.GOVUK_PAY_PAYMENT_DESCRIPTION.format(
                reference=order.reference,
            ),
            'return_url': settings.GOVUK_PAY_RETURN_URL.format(
                public_token=order.public_token,
                session_id=session.id,
            ),
        }

    @pytest.mark.parametrize(
        'disallowed_status', (
            OrderStatus.draft,
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_exception_if_order_in_disallowed_status(self, disallowed_status):
        """
        Test that if the order is not in one of the allowed statuses, the method raises
        APIConflictException.
        """
        assert PaymentGatewaySession.objects.count() == 0

        order = OrderFactory(status=disallowed_status)

        with pytest.raises(APIConflictException):
            PaymentGatewaySession.objects.create_from_order(order)

        # test no session created
        assert PaymentGatewaySession.objects.count() == 0

    def test_exception_if_refresh_updates_order_status_to_paid(self, requests_mock):
        """
        Test that if the system is not up-to-date, the order is in quote_accepted
        but the GOV.UK payment happens, the method triggers a check on existing
        sessions, realises that one finished successfully and records the payment
        marking the order as 'paid'.
        For this reason, the method raises APIConflictException as no other payment can be started.
        """
        # set up db
        order = OrderWithAcceptedQuoteFactory()
        existing_session = PaymentGatewaySessionFactory(
            order=order,
            status=PaymentGatewaySessionStatus.STARTED,
        )

        # mock GOV.UK requests used to refresh the payment session,
        # GOV.UK Pay says that the payment completed successfully
        requests_mock.get(
            govuk_url(f'payments/{existing_session.govuk_payment_id}'),
            status_code=200,
            json={
                'amount': order.total_cost,
                'state': {'status': 'success'},
                'email': 'email@example.com',
                'created_date': '2018-02-13T14:56:56.734Z',
                'reference': '12345',
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

        with pytest.raises(APIConflictException):
            PaymentGatewaySession.objects.create_from_order(order)

        # check session record
        existing_session.refresh_from_db()
        assert existing_session.status == PaymentGatewaySessionStatus.SUCCESS

        # check order and payment
        order.refresh_from_db()
        assert order.status == OrderStatus.paid

        assert Payment.objects.count() == 1
        payment = Payment.objects.first()

        assert payment.amount == order.total_cost
        assert payment.method == PaymentMethod.CARD
        assert payment.received_on == dateutil_parse('2018-02-13').date()
        assert payment.transaction_reference == '12345'
        assert payment.cardholder_name == 'John Doe'
        assert payment.billing_address_1 == 'line 1 address'
        assert payment.billing_address_2 == 'line 2 address'
        assert payment.billing_address_town == 'London'
        assert payment.billing_address_postcode == 'SW1A 1AA'
        assert payment.billing_address_country == 'GB'
        assert payment.billing_email == 'email@example.com'
        assert payment.card_brand == 'Visa'

    @pytest.mark.parametrize('govuk_status_code', (400, 401, 422, 500))
    def test_exception_if_govuk_pay_errors_when_creating(
        self, govuk_status_code, requests_mock,
    ):
        """
        Test that if GOV.UK Pay errors whilst creating a new payment, the method raises
        GOVUKPayAPIException.

        Possible GOV.UK Pay errors:
        - 400 - BAD REQUEST
        - 401 - UNAUTHORIZED
        - 422 - UNPROCESSABLE ENTITY
        - 500 - INTERNAL SERVER ERROR
        """
        requests_mock.post(
            govuk_url('payments'),
            status_code=govuk_status_code,
        )

        assert PaymentGatewaySession.objects.count() == 0

        order = OrderWithAcceptedQuoteFactory()

        with pytest.raises(GOVUKPayAPIException):
            PaymentGatewaySession.objects.create_from_order(order)

        assert PaymentGatewaySession.objects.count() == 0

    @pytest.mark.parametrize('govuk_status_code', (400, 401, 404, 409, 500))
    def test_exception_if_govuk_pay_errors_when_cancelling(
        self, govuk_status_code, requests_mock,
    ):
        """
        Test that if GOV.UK Pay errors whilst cancelling some other ongoing
        sessions/payments, the method raises GOVUKPayAPIException to keep the system consistent.

        Possible GOV.UK Pay errors when cancelling:
        - 400 - BAD REQUEST
        - 401 - UNAUTHORIZED
        - 404 - NOT FOUND
        - 409 - CONFLICT
        - 500 - INTERNAL SERVER ERROR
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

        assert PaymentGatewaySession.objects.count() == 1

        with pytest.raises(GOVUKPayAPIException):
            PaymentGatewaySession.objects.create_from_order(order)

        assert PaymentGatewaySession.objects.count() == 1

    def test_ongoing(self):
        """
        Test that given:
            session 1 - order 1 - status created
            session 2 - order 1 - status submitted
            session 3 - order 1 - status failed
            session 4 - order 2 - status started
            session 5 - order 2 - status success
            session 6 - order 2 - status cancelled

        the method .ongoing() on the queryset only returns the sessions
        which are considered not finished.
        """
        order1, order2 = OrderWithAcceptedQuoteFactory.create_batch(2)

        order1_sessions = PaymentGatewaySessionFactory.create_batch(
            3,
            order=order1,
            status=factory.Iterator([
                PaymentGatewaySessionStatus.CREATED,
                PaymentGatewaySessionStatus.SUBMITTED,
                PaymentGatewaySessionStatus.FAILED,
            ]),
        )
        order2_sessions = PaymentGatewaySessionFactory.create_batch(
            3,
            order=order2,
            status=factory.Iterator([
                PaymentGatewaySessionStatus.STARTED,
                PaymentGatewaySessionStatus.SUCCESS,
                PaymentGatewaySessionStatus.CANCELLED,
            ]),
        )

        # test qs without filters
        qs = PaymentGatewaySession.objects.ongoing()
        assert set(qs.values_list('id', flat=True)) == {
            order1_sessions[0].id,
            order1_sessions[1].id,
            order2_sessions[0].id,
        }

        # test qs with order filter
        qs = PaymentGatewaySession.objects.filter(order=order1).ongoing()
        assert set(qs.values_list('id', flat=True)) == {
            order1_sessions[0].id,
            order1_sessions[1].id,
        }
