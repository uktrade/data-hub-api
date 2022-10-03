import logging
from unittest import mock
from unittest.mock import patch

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from requests import ConnectTimeout
from rest_framework import status

from datahub.company.tasks import (
    automatic_contact_archive,
    update_contact_consent,
)
from datahub.company.tasks.contact import (
    schedule_automatic_contact_archive,
    schedule_update_contact_consent,
)
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.queues.errors import RetryError
from datahub.core.test_utils import HawkMockJSONResponse


def generate_hawk_response(payload):
    """Mocks HAWK server validation for content."""
    return HawkMockJSONResponse(
        api_id=settings.COMPANY_MATCHING_HAWK_ID,
        api_key=settings.COMPANY_MATCHING_HAWK_KEY,
        response=payload,
    )


@pytest.mark.django_db
class TestConsentServiceTask:
    """
    tests for the task that sends email marketing consent status to the
    DIT consent service / legal basis API
    """

    @override_settings(
        CONSENT_SERVICE_BASE_URL=None,
    )
    def test_not_configured_error(
            self,
    ):
        """
        Test that if feature flag is enabled, but environment variables are not set
        then task will throw a caught exception and no retries or updates will occur
        """
        update_succeeds = update_contact_consent('example@example.com', True)
        assert update_succeeds is False

    @pytest.mark.parametrize(
        'email_address, accepts_dit_email_marketing, modified_at',
        (
            ('example@example.com', True, None),
            ('example@example.com', False, None),
            ('example@example.com', True, '2020-01-01-12:00:00Z'),
            ('example@example.com', False, '2020-01-01-12:00:00Z'),
        ),
    )
    def test_task_makes_http_request(
            self,
            requests_mock,
            email_address,
            accepts_dit_email_marketing,
            modified_at,
    ):
        """
        Ensure correct http request with correct payload is generated when task
        executes.
        """
        matcher = requests_mock.post('/api/v1/person/', text=generate_hawk_response({}),
                                     status_code=status.HTTP_201_CREATED)
        update_contact_consent(
            email_address,
            accepts_dit_email_marketing,
            modified_at=modified_at,
        )
        assert matcher.called_once
        expected = {
            'email': email_address,
            'consents': ['email_marketing'] if accepts_dit_email_marketing else [],
        }
        if modified_at:
            expected['modified_at'] = modified_at

        assert matcher.last_request.json() == expected

    @pytest.mark.parametrize(
        'status_code',
        (
            (status.HTTP_404_NOT_FOUND),
            (status.HTTP_403_FORBIDDEN),
            (status.HTTP_500_INTERNAL_SERVER_ERROR),
        ),
    )
    def test_task_retries_on_request_exceptions(
            self,
            requests_mock,
            status_code,
    ):
        """
        Test to ensure that rq receives exceptions like 5xx, 404 and then will retry based on
        job_scheduler configuration
        """
        matcher = requests_mock.post(
            '/api/v1/person/',
            text=generate_hawk_response({}),
            status_code=status_code,
        )
        with pytest.raises(RetryError):
            update_contact_consent('example@example.com', True)
        assert matcher.called_once

    @patch('datahub.company.consent.APIClient.request', side_effect=ConnectTimeout)
    def test_task_retries_on_connect_timeout(
            self,
            mock_post,
    ):
        """
        Test to ensure that RQ retries on connect timeout by virtue of the exception forcing
        a retry within RQ and configured settings
        """
        with pytest.raises(RetryError):
            update_contact_consent('example@example.com', True)
        assert mock_post.called

    @patch('datahub.company.consent.APIClient.request', side_effect=Exception)
    def test_task_doesnt_retry_on_other_exception(
            self,
            mock_post,
    ):
        """
        Test to ensure that RQ raises on non-requests exception
        """
        update_succeeds = update_contact_consent('example@example.com', True)
        assert mock_post.called
        assert update_succeeds is False

    @pytest.mark.parametrize(
        'status_code',
        (
            (status.HTTP_200_OK),
            (status.HTTP_201_CREATED),
        ),
    )
    def test_update_succeeds(
            self,
            requests_mock,
            status_code,
    ):
        """
        Test success occurs when update succeeds
        """
        matcher = requests_mock.post(
            '/api/v1/person/',
            text=generate_hawk_response({}),
            status_code=status_code,
        )

        update_success = update_contact_consent('example@example.com', True)

        assert matcher.called_once
        assert update_success is True

    @pytest.mark.parametrize(
        'bad_email',
        (
            None,
            '',
            '  ',
        ),
    )
    def test_none_or_empty_email_assigned_fails(
        self,
        requests_mock,
        bad_email,
    ):
        matcher = requests_mock.post(
            '/api/v1/person/',
            text=generate_hawk_response({}),
            status_code=status.HTTP_201_CREATED,
        )

        update_success = update_contact_consent(bad_email, False)

        assert not matcher.called_once
        assert update_success is False

    def test_job_schedules_with_correct_update_contact_consent_details(self):
        actual_job = schedule_update_contact_consent('example@example.com', True)

        assert actual_job is not None
        assert actual_job._func_name == 'datahub.company.tasks.contact.update_contact_consent'
        assert actual_job._args == ('example@example.com', True, None)
        assert actual_job.retries_left == 5
        assert actual_job.retry_intervals == [30, 961, 1024, 1089, 1156]
        assert actual_job.origin == 'short-running'


@pytest.mark.django_db
class TestContactArchiveTask:
    """
    Tests for the task that archives contacts
    """

    @pytest.mark.parametrize(
        'lock_acquired, call_count',
        (
            (False, 0),
            (True, 1),
        ),
    )
    def test_lock(
        self,
        monkeypatch,
        lock_acquired,
        call_count,
    ):
        """
        Test that the task doesn't run if it cannot acquire the advisory_lock
        """
        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.company.tasks.contact.advisory_lock',
            mock_advisory_lock,
        )
        mock_automatic_contact_archive = mock.Mock()
        monkeypatch.setattr(
            'datahub.company.tasks.contact._automatic_contact_archive',
            mock_automatic_contact_archive,
        )
        automatic_contact_archive()
        assert mock_automatic_contact_archive.call_count == call_count

    def test_limit(self):
        """
        Test contact archiving query limit
        """
        limit = 2
        contacts = [ContactFactory(company=CompanyFactory(archived=True)) for _ in range(3)]
        automatic_contact_archive(limit=limit)

        count = 0
        for contact in contacts:
            contact.refresh_from_db()
            if contact.archived:
                count += 1
        assert count == limit

    @pytest.mark.parametrize('simulate', (True, False))
    def test_simulate(self, caplog, simulate):
        """
        Test contact archiving simulate flag
        """
        caplog.set_level(logging.INFO, logger='datahub.company.tasks.contact')
        date = timezone.now() - relativedelta(days=10)
        with freeze_time(date):
            company1 = CompanyFactory()
            company2 = CompanyFactory(archived=True)
            contact1 = ContactFactory(company=company1)
            contact2 = ContactFactory(company=company2)
        automatic_contact_archive(simulate=simulate)
        contact1.refresh_from_db()
        contact2.refresh_from_db()
        if simulate:
            assert caplog.messages == [
                f'[SIMULATION] Automatically archived contact: {contact2.id}',
            ]
        else:
            assert contact1.archived is False
            assert contact2.archived is True
            assert caplog.messages == [f'Automatically archived contact: {contact2.id}']

    @pytest.mark.parametrize(
        'contacts, message',
        (
            (
                (False, False, False),
                'datahub.company.tasks.automatic_contact_archive archived: 0',
            ),
            (
                (False, False, True),
                'datahub.company.tasks.automatic_contact_archive archived: 1',
            ),
            (
                (True, True, True),
                'datahub.company.tasks.automatic_contact_archive archived: 3',
            ),
        ),
    )
    def test_realtime_messages_sent(
        self,
        monkeypatch,
        contacts,
        message,
    ):
        """
        Test that appropriate realtime messaging is sent which reflects the archiving actions
        """
        for is_archived in contacts:
            company = CompanyFactory(archived=is_archived)
            ContactFactory(company=company)

        mock_send_realtime_message = mock.Mock()
        monkeypatch.setattr(
            'datahub.company.tasks.contact.send_realtime_message',
            mock_send_realtime_message,
        )
        automatic_contact_archive()
        mock_send_realtime_message.assert_called_once_with(message)

    def test_archive_no_updates(self):
        """
        Test contact archiving with no updates on contacts
        """
        date = timezone.now() - relativedelta(days=10)
        with freeze_time(date):
            company1 = CompanyFactory()
            company2 = CompanyFactory()
            contact1 = ContactFactory(company=company1)
            contact2 = ContactFactory(company=company2)
            contact3 = ContactFactory(company=company2)
            for contact in [contact1, contact2, contact3]:
                assert contact.archived is False
                assert contact.archived_reason is None
                assert contact.archived_on is None

            # run task twice expecting same result
            for _ in range(2):
                automatic_contact_archive(limit=200)
                for contact in [contact1, contact2, contact3]:
                    contact.refresh_from_db()
                    assert contact.archived is False
                    assert contact.archived_reason is None
                    assert contact.archived_on is None

    def test_archive_with_updates(self):
        """
        Test contact archiving with updates on correct contacts
        """
        date = timezone.now() - relativedelta(days=10)
        with freeze_time(date):
            company1 = CompanyFactory()
            company2 = CompanyFactory(archived=True)
            contact1 = ContactFactory(company=company1)
            contact2 = ContactFactory(company=company2)
            contact3 = ContactFactory(company=company2)
            for contact in [contact1, contact2, contact3]:
                assert contact.archived is False
                assert contact.archived_reason is None
                assert contact.archived_on is None

            # run task twice expecting same result
            for _ in range(2):
                automatic_contact_archive(limit=200)

                contact1.refresh_from_db()
                contact2.refresh_from_db()
                contact3.refresh_from_db()
                assert contact1.archived is False
                assert contact2.archived is True
                assert contact3.archived is True
                assert contact1.archived_reason is None
                assert contact2.archived_reason is not None
                assert contact3.archived_reason is not None
                assert contact1.archived_on is None
                assert contact2.archived_on == date
                assert contact3.archived_on == date

        # run again at later time expecting no changes
        automatic_contact_archive(limit=200)

        contact1.refresh_from_db()
        contact2.refresh_from_db()
        contact3.refresh_from_db()
        assert contact1.archived is False
        assert contact2.archived is True
        assert contact3.archived is True
        assert contact1.archived_reason is None
        assert contact2.archived_reason is not None
        assert contact3.archived_reason is not None
        assert contact1.archived_on is None
        assert contact2.archived_on == date
        assert contact3.archived_on == date

    def test_job_schedules_with_correct_contact_archive_details(self):
        actual_job = schedule_automatic_contact_archive(limit=1000, simulate=True)

        assert actual_job is not None
        assert actual_job._func_name == 'datahub.company.tasks.contact.automatic_contact_archive'
        assert actual_job._args == (1000, True)
        assert actual_job.retries_left == 3
        assert actual_job.origin == 'long-running'
