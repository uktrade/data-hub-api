import re

import factory
import pytest
from freezegun import freeze_time

from datahub.omis.payment.constants import PaymentGatewaySessionStatus
from datahub.omis.payment.govukpay import govuk_url
from datahub.omis.payment.tasks import refresh_pending_payment_gateway_sessions
from datahub.omis.payment.test.factories import PaymentGatewaySessionFactory


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestRefreshPendingPaymentGatewaySessions:
    """
    Tests for the `refresh_pending_payment_gateway_sessions` and related
    `refresh_payment_gateway_session` tasks.
    """

    def test_refresh(self, requests_mock):
        """
        Test that only ongoing sessions older than 60 minutes are refreshed against GOV.UK Pay.
        Note that the value '60 minutes' is a parameter initialised in the test
        and not part of the logic of the task.
        """
        # mock call to GOV.UK Pay
        requests_mock.register_uri(
            'GET',
            re.compile(govuk_url(f'payments/*')),
            json={'state': {'status': 'failed'}},
        )

        # populate db
        data = (
            # shouldn't be included because modified_on == 59 mins ago
            ('2017-04-18 19:01', PaymentGatewaySessionStatus.STARTED),

            # shouldn't be included because status != 'ongoing'
            ('2017-04-18 18:59', PaymentGatewaySessionStatus.SUCCESS),
            ('2017-04-18 18:59', PaymentGatewaySessionStatus.FAILED),
            ('2017-04-18 18:59', PaymentGatewaySessionStatus.CANCELLED),
            ('2017-04-18 18:59', PaymentGatewaySessionStatus.ERROR),

            # should be included because modified_on >= 60 mins ago
            ('2017-04-18 19:00', PaymentGatewaySessionStatus.CREATED),
            ('2017-04-18 18:59', PaymentGatewaySessionStatus.STARTED),
            ('2017-04-17 20:00', PaymentGatewaySessionStatus.SUBMITTED),
        )
        sessions = []
        for frozen_time, session_status in data:
            with freeze_time(frozen_time):
                sessions.append(PaymentGatewaySessionFactory(status=session_status))

        # make call
        with freeze_time('2017-04-18 20:00'):  # mocking now
            refresh_pending_payment_gateway_sessions(age_check=60)

        # check result
        assert requests_mock.call_count == 3
        for session in sessions[-3:]:
            session.refresh_from_db()
            assert session.status == PaymentGatewaySessionStatus.FAILED

    @freeze_time('2017-04-18 20:00')
    def test_one_failed_refresh_doesnt_stop_others(self, requests_mock):
        """
        Test that if one refresh fails, the other ones are still carried on
        and committed to the databasea.

        In this example, pay-1 and pay-3 should get refreshed whilst pay-2
        errors and shouldn't get refreshed.
        """
        # mock calls to GOV.UK Pay
        govuk_payment_ids = ['pay-1', 'pay-2', 'pay-3']
        requests_mock.get(
            govuk_url(f'payments/{govuk_payment_ids[0]}'), status_code=200,
            json={'state': {'status': 'failed'}},
        )
        requests_mock.get(
            govuk_url(f'payments/{govuk_payment_ids[1]}'), status_code=500,
        )
        requests_mock.get(
            govuk_url(f'payments/{govuk_payment_ids[2]}'), status_code=200,
            json={'state': {'status': 'failed'}},
        )

        # populate db
        sessions = PaymentGatewaySessionFactory.create_batch(
            3,
            status=PaymentGatewaySessionStatus.STARTED,
            govuk_payment_id=factory.Iterator(govuk_payment_ids),
        )

        # make call
        refresh_pending_payment_gateway_sessions(age_check=0)

        # check result
        for session in sessions:
            session.refresh_from_db()

        assert requests_mock.call_count == 3
        assert sessions[0].status == PaymentGatewaySessionStatus.FAILED
        assert sessions[1].status == PaymentGatewaySessionStatus.STARTED
        assert sessions[2].status == PaymentGatewaySessionStatus.FAILED
