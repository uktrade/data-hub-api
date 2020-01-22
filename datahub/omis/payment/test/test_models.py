from unittest import mock

import pytest
from dateutil.parser import parse as dateutil_parse

from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import OrderWithAcceptedQuoteFactory
from datahub.omis.payment.constants import PaymentGatewaySessionStatus, PaymentMethod
from datahub.omis.payment.govukpay import govuk_url, GOVUKPayAPIException
from datahub.omis.payment.models import Payment, PaymentGatewaySession
from datahub.omis.payment.test.factories import PaymentGatewaySessionFactory


class TestPaymentGatewaySessionIsFinished:
    """Tests for the `is_finished` method."""

    @pytest.mark.parametrize(
        'status,finished',
        (
            (PaymentGatewaySessionStatus.CREATED, False),
            (PaymentGatewaySessionStatus.STARTED, False),
            (PaymentGatewaySessionStatus.SUBMITTED, False),
            (PaymentGatewaySessionStatus.SUCCESS, True),
            (PaymentGatewaySessionStatus.FAILED, True),
            (PaymentGatewaySessionStatus.CANCELLED, True),
            (PaymentGatewaySessionStatus.ERROR, True),
        ),
    )
    def test_value(self, status, finished):
        """
        Test the return value of `is_finished` with different values of session.status.
        """
        session = PaymentGatewaySession(status=status)
        assert session.is_finished() == finished


class TestPaymentGatewaySessionGetPaymentURL:
    """Tests for the `get_payment_url` method."""

    def test_with_value(self, requests_mock):
        """
        Test the value returned when the GOV.UK Pay response data includes next_url.
        """
        govuk_payment_id = '123abc123abc123abc123abc12'
        next_url = 'https://payment.example.com/123abc'
        requests_mock.get(
            govuk_url(f'payments/{govuk_payment_id}'),
            status_code=200,
            json={
                'state': {'status': 'started', 'finished': False},
                'payment_id': govuk_payment_id,
                '_links': {
                    'next_url': {
                        'href': next_url,
                        'method': 'GET',
                    },
                },
            },
        )

        session = PaymentGatewaySession(govuk_payment_id=govuk_payment_id)
        assert session.get_payment_url() == next_url

    def test_without_value(self, requests_mock):
        """
        Test that an empty string is returned when the GOV.UK Pay response data
        doesn't include next_url.
        """
        govuk_payment_id = '123abc123abc123abc123abc12'
        requests_mock.get(
            govuk_url(f'payments/{govuk_payment_id}'),
            status_code=200,
            json={
                'state': {'status': 'cancelled', 'finished': True},
                'payment_id': govuk_payment_id,
                '_links': {
                    'next_url': None,
                },
            },
        )

        session = PaymentGatewaySession(govuk_payment_id=govuk_payment_id)
        assert session.get_payment_url() == ''

    @pytest.mark.parametrize(
        'session_status',
        (
            PaymentGatewaySessionStatus.SUCCESS,
            PaymentGatewaySessionStatus.FAILED,
            PaymentGatewaySessionStatus.CANCELLED,
            PaymentGatewaySessionStatus.ERROR,
        ),
    )
    def test_doesnt_call_govuk_pay_if_finished(self, session_status, requests_mock):
        """
        Test that if the payment gateway session is finished, no call to GOV.UK Pay is made
        and the method returns an empty string.
        """
        session = PaymentGatewaySession(
            status=session_status,
            govuk_payment_id='123abc123abc123abc123abc12',
        )
        assert session.get_payment_url() == ''
        assert not requests_mock.called


@pytest.mark.django_db
class TestPaymentGatewaySessionRefresh:
    """Tests for the `refresh_from_govuk_payment` method."""

    @pytest.mark.parametrize(
        'status', (
            PaymentGatewaySessionStatus.SUCCESS,
            PaymentGatewaySessionStatus.FAILED,
            PaymentGatewaySessionStatus.CANCELLED,
            PaymentGatewaySessionStatus.ERROR,
        ),
    )
    def test_already_finished_doesnt_do_anything(self, status, requests_mock):
        """
        Test that if the payment gateway session is already finished, the system
        doesn't call GOV.UK Pay as it's already in its end state.
        """
        session = PaymentGatewaySession(status=status)

        assert not session.refresh_from_govuk_payment()
        assert not requests_mock.called

    @pytest.mark.parametrize(
        'status',
        (
            PaymentGatewaySessionStatus.CREATED,
            PaymentGatewaySessionStatus.STARTED,
            PaymentGatewaySessionStatus.SUBMITTED,
        ),
    )
    def test_with_unchanged_govuk_payment_status_doesnt_change_anything(
        self, status, requests_mock,
    ):
        """
        Test that if the GOV.UK payment status is the same as the payment gateway session one,
        (meaning that the payment gateway session is up-to-date), the record is not changed.
        """
        session = PaymentGatewaySession(status=status)
        url = govuk_url(f'payments/{session.govuk_payment_id}')
        requests_mock.get(
            url, status_code=200, json={
                'state': {'status': status, 'finished': False},
            },
        )

        assert not session.refresh_from_govuk_payment()
        assert session.status == status
        assert Payment.objects.count() == 0

        assert requests_mock.call_count == 1

    @pytest.mark.parametrize(
        'status',
        (
            status[0] for status in PaymentGatewaySessionStatus
            if status[0] != PaymentGatewaySessionStatus.SUCCESS
        ),
    )
    def test_with_different_govuk_payment_status_updates_session(self, status, requests_mock):
        """
        Test that if the GOV.UK payment status is not the same as the payment gateway session one,
        the record is updated.
        """
        # choose an initial status != from the govuk one to test the update
        initial_status = PaymentGatewaySessionStatus.CREATED
        if initial_status == status:
            initial_status = PaymentGatewaySessionStatus.STARTED

        session = PaymentGatewaySessionFactory(status=initial_status)
        url = govuk_url(f'payments/{session.govuk_payment_id}')
        requests_mock.get(
            url, status_code=200, json={
                'state': {'status': status},
            },
        )

        assert session.refresh_from_govuk_payment()

        session.refresh_from_db()
        assert session.status == status

        assert requests_mock.call_count == 1

    def test_with_govuk_payment_success_updates_order(self, requests_mock):
        """
        Test that if the GOV.UK payment status is `success` and the payment gateway session is
        out of date, the record is updated, the related order marked as `paid` and an OMIS
        `payment.Payment` record created from the GOV.UK response data one.
        """
        order = OrderWithAcceptedQuoteFactory()
        session = PaymentGatewaySessionFactory(
            status=PaymentGatewaySessionStatus.CREATED,
            order=order,
        )
        url = govuk_url(f'payments/{session.govuk_payment_id}')
        response_json = {
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
        }
        requests_mock.get(url, status_code=200, json=response_json)

        assert session.refresh_from_govuk_payment()

        # check session
        session.refresh_from_db()
        assert session.status == PaymentGatewaySessionStatus.SUCCESS

        # check order
        order.refresh_from_db()
        assert order.status == OrderStatus.paid

        # check payment object
        assert Payment.objects.filter(order=order).count() == 1

        payment = Payment.objects.filter(order=order).first()
        assert payment.amount == response_json['amount']
        assert payment.method == PaymentMethod.CARD
        assert payment.received_on == dateutil_parse('2018-02-13').date()
        assert payment.transaction_reference == '12345'

        assert payment.cardholder_name == 'John Doe'
        assert payment.card_brand == 'Visa'
        assert payment.billing_email == 'email@example.com'
        assert payment.billing_address_1 == 'line 1 address'
        assert payment.billing_address_2 == 'line 2 address'
        assert payment.billing_address_town == 'London'
        assert payment.billing_address_postcode == 'SW1A 1AA'
        assert payment.billing_address_country == 'GB'

        assert requests_mock.call_count == 1

    def test_atomicity_when_govuk_pay_errors(self, requests_mock):
        """
        Test that if GOV.UK Pay errors, none of the changes persists.
        """
        session = PaymentGatewaySessionFactory()
        original_session_status = session.status

        url = govuk_url(f'payments/{session.govuk_payment_id}')
        requests_mock.get(url, status_code=500)

        with pytest.raises(GOVUKPayAPIException):
            assert session.refresh_from_govuk_payment()

        session.refresh_from_db()
        assert session.status == original_session_status

        assert requests_mock.call_count == 1

    def test_atomicity_when_session_save_errors(self, requests_mock):
        """
        Test that if the PaymentGatewaySession.save() call fails, none of the changes persists.
        """
        session = PaymentGatewaySessionFactory()
        original_session_status = session.status
        url = govuk_url(f'payments/{session.govuk_payment_id}')
        requests_mock.get(
            url, status_code=200, json={
                'state': {'status': 'success'},
            },
        )
        session.save = mock.MagicMock(side_effect=Exception())

        with pytest.raises(Exception):
            session.refresh_from_govuk_payment()

        session.refresh_from_db()
        assert session.status == original_session_status

        assert requests_mock.call_count == 1

    def test_atomicity_when_order_save_errors(self, requests_mock):
        """
        Test that if the order.mark_as_paid() call fails, non of the changes persists.
        """
        session = PaymentGatewaySessionFactory()
        original_session_status = session.status
        url = govuk_url(f'payments/{session.govuk_payment_id}')
        requests_mock.get(
            url, status_code=200, json={
                'state': {'status': 'success'},
            },
        )
        session.order.mark_as_paid = mock.MagicMock(side_effect=Exception())

        with pytest.raises(Exception):
            session.refresh_from_govuk_payment()

        session.refresh_from_db()
        assert session.status == original_session_status

        assert requests_mock.call_count == 1


@pytest.mark.django_db
class TestPaymentGatewaySessionCancel:
    """Tests for the `cancel` method."""

    def test_cancel_updates_session(self, requests_mock):
        """
        Test that if GOV.UK Pay cancels and acknowledges the change,
        the session object is updated.
        """
        session = PaymentGatewaySessionFactory()
        requests_mock.post(
            govuk_url(f'payments/{session.govuk_payment_id}/cancel'),
            status_code=204,
        )
        requests_mock.get(
            govuk_url(f'payments/{session.govuk_payment_id}'),
            status_code=200,
            json={'state': {'status': 'cancelled'}},
        )

        session.cancel()

        session.refresh_from_db()
        assert session.status == PaymentGatewaySessionStatus.CANCELLED

        assert requests_mock.call_count == 2

    def test_with_govuk_pay_erroring_when_cancelling(self, requests_mock):
        """
        Test that if GOV.UK Pay errors when cancelling the payment,
        the session object is not updated.
        """
        session = PaymentGatewaySessionFactory()
        original_session_status = session.status
        requests_mock.post(
            govuk_url(f'payments/{session.govuk_payment_id}/cancel'),
            status_code=500,
        )

        with pytest.raises(GOVUKPayAPIException):
            session.cancel()

        session.refresh_from_db()
        assert session.status == original_session_status

        assert requests_mock.call_count == 1

    def test_with_govuk_pay_erroring_when_refreshing(self, requests_mock):
        """
        Test that if GOV.UK Pay cancels the payment but errors when
        refreshing the session, the session object is not updated
        (but the GOV.UK payment is still cancelled).
        This is okay as the session object will get refreshed at the next
        opportunity.
        """
        session = PaymentGatewaySessionFactory()
        original_session_status = session.status
        requests_mock.post(
            govuk_url(f'payments/{session.govuk_payment_id}/cancel'),
            status_code=204,
        )
        requests_mock.get(
            govuk_url(f'payments/{session.govuk_payment_id}'),
            status_code=500,
        )

        with pytest.raises(GOVUKPayAPIException):
            session.cancel()

        session.refresh_from_db()
        assert session.status == original_session_status

        assert requests_mock.call_count == 2
