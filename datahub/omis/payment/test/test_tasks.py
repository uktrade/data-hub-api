import logging
import re
from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from datahub.omis.payment.constants import PaymentGatewaySessionStatus
from datahub.omis.payment.govukpay import govuk_url
from datahub.omis.payment.tasks import (
    refresh_payment_gateway_session,
    refresh_pending_payment_gateway_sessions,
)
from datahub.omis.payment.test.factories import PaymentGatewaySessionFactory


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestRefreshPendingPaymentGatewaySessions:
    """
    Tests for the `refresh_pending_payment_gateway_sessions` and related
    `refresh_payment_gateway_session` tasks.
    """

    def mock_sessions(self, requests_mock):
        # mock call to GOV.UK Pay
        requests_mock.register_uri(
            'GET',
            re.compile(govuk_url('payments/*')),
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

        return sessions

    def test_schedule_refresh_payment_gateway_session(self, monkeypatch, requests_mock):
        """
        Test that only ongoing sessions older than 60 minutes are refreshed against GOV.UK Pay.
        Note that the value '60 minutes' is a parameter initialised in the test
        and not part of the logic of the task.
        """
        self.mock_sessions(requests_mock)

        mock_schedule_refresh_payment_gateway_session = Mock()
        monkeypatch.setattr(
            'datahub.omis.payment.tasks.schedule_refresh_payment_gateway_session',
            mock_schedule_refresh_payment_gateway_session,
        )

        # make call
        with freeze_time('2017-04-18 20:00'):  # mocking now
            refresh_pending_payment_gateway_sessions(age_check=60)

        # check result
        assert mock_schedule_refresh_payment_gateway_session.call_count == 3

    def test_job_scheduler_schedule_refresh_payment_gateway_session(
            self, caplog, monkeypatch, requests_mock):
        self.mock_sessions(requests_mock)
        caplog.set_level(logging.INFO)

        # make call
        with freeze_time('2017-04-18 20:00'):  # mocking now
            refresh_pending_payment_gateway_sessions(age_check=60)

        # check result
        assert any(
            'schedule_refresh_payment_gateway_session'
            in message for message in caplog.messages
        )
        # assert mock_payment_tasks_job_scheduler.call_count == 3

    def test_refresh(self, monkeypatch, requests_mock):
        """
        Test that only ongoing sessions older than 60 minutes are refreshed against GOV.UK Pay.
        Note that the value '60 minutes' is a parameter initialised in the test
        and not part of the logic of the task.
        """
        sessions = self.mock_sessions(requests_mock)

        # make call
        with freeze_time('2017-04-18 20:00'):  # mocking now
            for session in sessions:
                refresh_payment_gateway_session(session_id=session.id)

        # check result
        for session in sessions[-3:]:
            session.refresh_from_db()
            assert session.status == PaymentGatewaySessionStatus.FAILED
