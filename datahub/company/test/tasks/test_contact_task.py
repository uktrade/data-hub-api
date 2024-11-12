import json
import logging
import uuid

from unittest import mock
from unittest.mock import patch

import boto3
import pytest

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from moto import mock_aws
from requests import ConnectTimeout
from rest_framework import status

from datahub.company.models.contact import Contact
from datahub.company.tasks import (
    automatic_contact_archive,
    update_contact_consent,
)
from datahub.company.tasks.contact import (
    BUCKET,
    CONSENT_PREFIX,
    ContactConsentIngestionTask,
    ingest_contact_consent_data,
    REGION,
    schedule_automatic_contact_archive,
    schedule_update_contact_consent,
)
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.queues.errors import RetryError
from datahub.core.test_utils import HawkMockJSONResponse


def generate_hawk_response(payload):
    """Mocks HAWK server validation for content."""
    return HawkMockJSONResponse(
        api_id=settings.CONSENT_SERVICE_HAWK_ID,
        api_key=settings.CONSENT_SERVICE_HAWK_KEY,
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
        matcher = requests_mock.post(
            '/api/v1/person/',
            text=generate_hawk_response({}),
            status_code=status.HTTP_201_CREATED,
        )
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


@pytest.fixture
def test_files():
    files = [
        f'FILE_A/{uuid.uuid4()}/full_ingestion.jsonl',
        f'FILE_B/{uuid.uuid4()}/full_ingestion.jsonl',
        f'FILE_C/{uuid.uuid4()}/full_ingestion.jsonl',
    ]
    return list(map(lambda x: CONSENT_PREFIX + x, files))


@mock_aws
def setup_s3_bucket(bucket_name, test_files):
    mock_s3_client = _create_bucket(bucket_name)
    for file in test_files:
        mock_s3_client.put_object(Bucket=bucket_name, Key=file, Body=json.dumps('Test contents'))


def _create_bucket(bucket_name):
    mock_s3_client = boto3.client('s3', REGION)
    mock_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': REGION},
    )

    return mock_s3_client


@mock_aws
def upload_file_to_s3(bucket_name, file_key, contents):
    mock_s3_client = _create_bucket(bucket_name)
    mock_s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=contents)


@pytest.mark.django_db
class TestContactConsentIngestionTaskScheduler:

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
        mock_ingest_contact_consent_data = mock.Mock()
        monkeypatch.setattr(
            'datahub.company.tasks.contact.ContactConsentIngestionTask.ingest',
            mock_ingest_contact_consent_data,
        )
        ingest_contact_consent_data()
        assert mock_ingest_contact_consent_data.call_count == call_count


@pytest.mark.django_db
class TestContactConsentIngestionTask:

    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_ingest_with_exception_logs_error_and_reraises_original_exception(self, test_files):
        """
        Test that the task can catch and log any unhandled exceptions
        """
        setup_s3_bucket(BUCKET, test_files)

        with mock.patch.object(
            ContactConsentIngestionTask,
            'sync_file_with_database',
            side_effect=AttributeError('Original error message'),
        ), pytest.raises(AttributeError, match='Original error message'):
            task = ContactConsentIngestionTask()
            task.ingest()

    @mock_aws
    def test_ingest_with_empty_s3_bucket_does_not_call_sync_or_delete(self):
        """
        Test that the task can handle an empty S3 bucket
        """
        setup_s3_bucket(BUCKET, [])
        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            sync_file_with_database=mock.DEFAULT,
            delete_file=mock.DEFAULT,
        ):
            task.ingest()
            task.sync_file_with_database.assert_not_called()
            task.delete_file.assert_not_called()

    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_ingest_calls_sync_with_correct_files_order(self, test_files):
        """
        Test that the ingest calls the sync with the files in correct order
        """
        setup_s3_bucket(BUCKET, test_files)
        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            sync_file_with_database=mock.DEFAULT,
            delete_file=mock.DEFAULT,
        ):
            task.ingest()
            task.sync_file_with_database.assert_has_calls(
                [mock.call(mock.ANY, file) for file in test_files],
            )

    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_ingest_calls_delete_for_all_files(
        self,
        test_files,
    ):
        """
        Test that the ingest calls delete with the files in correct order
        """
        setup_s3_bucket(BUCKET, test_files)
        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            sync_file_with_database=mock.DEFAULT,
            delete_file=mock.DEFAULT,
        ):
            task.ingest()
            task.delete_file.assert_has_calls(
                [mock.call(mock.ANY, file) for file in test_files],
            )

    @mock_aws
    def test_sync_file_with_row_without_email_key(self):
        """
        Test when a row is processed that has no email key it is skipped
        """
        contact = ContactFactory()
        row = {}
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(row))
        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data is None

    @mock_aws
    def test_sync_file_with_row_without_consents_key(self):
        """
        Test when a row is processed that has no consents key it is skipped
        """
        contact = ContactFactory()
        row = {'email': contact.email}
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(row))
        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data is None

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    def test_sync_file_without_matching_email_does_not_update_contact(self):
        """
        Test when a row has an email that does not match a contact no changes are made
        """
        row = {
            'email': 'not_matching@bar.com',
            'consents': [{'consent_domain': 'Domestic', 'email_contact_consent': True}],
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(row))
        contact = ContactFactory(consent_data='A')
        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data == 'A'
        assert Contact.objects.filter(email='not_matching@bar.com').first() is None

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    @pytest.mark.parametrize(
        'consent_data_last_modified,file_last_modified',
        (
            (
                '2024-08-02T12:00:00',
                '2023-07-20T12:00:00',
            ),
        ),
    )
    def test_sync_file_with_matching_email_but_last_modified_check_false_does_not_update_contact(
        self,
        consent_data_last_modified,
        file_last_modified,
    ):
        """
        Test when a row has an email that matches a contact the consent_data is updated
        """
        contact = ContactFactory(
            consent_data='A',
            consent_data_last_modified=consent_data_last_modified,
        )
        row = {
            'email': contact.email,
            'last_modified': file_last_modified,
            'consents': {'consent': True},
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(row))

        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data == 'A'

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    @pytest.mark.parametrize(
        'consent_data_last_modified,file_last_modified',
        (
            (
                '2023-07-20T12:00:00',
                '2024-08-02T12:00:00',
            ),
            (
                None,
                '2024-08-20T12:00:00',
            ),
            (
                '2024-08-20T12:00:00',
                None,
            ),
            (
                None,
                None,
            ),
        ),
    )
    def test_sync_file_with_matching_email_but_last_modified_check_true_does_update_contact(
        self,
        consent_data_last_modified,
        file_last_modified,
    ):
        """
        Test when a row has an email that matches a contact the consent_data is updated
        """
        contact = ContactFactory(
            consent_data='A',
            consent_data_last_modified=consent_data_last_modified,
        )
        row = {
            'email': contact.email,
            'last_modified': file_last_modified,
            'consents': {'consent': True},
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(row))

        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data == {'consent': True}

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    def test_sync_file_with_multiple_contacts_matching_email_does_update_contact(self):
        """
        Test when a row has an email that matches multiple contacts all contacts are updated
        """
        test_email = 'duplicate@test.com'
        ContactFactory.create_batch(
            3,
            email=test_email,
            consent_data='A',
            consent_data_last_modified='2023-07-20T12:00:00',
        )
        row = {
            'email': test_email,
            'last_modified': '2024-08-02T12:00:00',
            'consents': {'consent': True},
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(row))

        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        for contact in Contact.objects.filter(email=test_email):
            assert contact.consent_data == {'consent': True}

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=False)
    def test_sync_file_with_matching_email_but_ingest_setting_false_does_not_update_contact(self):
        """
        Test when a row has an email that matches a contact the consent_data is updated
        """
        contact = ContactFactory(
            consent_data='A',
            consent_data_last_modified='2023-07-20T12:00:00',
        )
        row = {
            'email': contact.email,
            'last_modified': '2024-08-02T12:00:00',
            'consents': {'consent': True},
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(row))

        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data == 'A'

    @mock_aws
    def test_delete_file_removes_file_using_boto3(self):
        """
        Test that the file is deleted from the bucket
        """
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, 'test')
        client = boto3.client('s3', REGION)

        ContactConsentIngestionTask().delete_file(client, filename)
        with pytest.raises(client.exceptions.NoSuchKey):
            client.get_object(
                Bucket=BUCKET,
                Key=filename,
            )
