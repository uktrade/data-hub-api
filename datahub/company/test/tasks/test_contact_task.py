import datetime
import json
import logging
import uuid
from unittest import mock

import boto3
import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from moto import mock_aws

from datahub.company.models.contact import Contact
from datahub.company.tasks import (
    automatic_contact_archive,
)
from datahub.company.tasks.contact import (
    BUCKET,
    CONSENT_PREFIX,
    REGION,
    ContactConsentIngestionTask,
    ingest_contact_consent_data,
    schedule_automatic_contact_archive,
)
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.test_utils import HawkMockJSONResponse
from datahub.ingest.models import IngestedObject
from datahub.ingest.test.factories import IngestedObjectFactory


def generate_hawk_response(payload):
    """Mocks HAWK server validation for content."""
    return HawkMockJSONResponse(
        api_id=settings.CONSENT_SERVICE_HAWK_ID,
        api_key=settings.CONSENT_SERVICE_HAWK_KEY,
        response=payload,
    )


@pytest.mark.django_db
class TestContactArchiveTask:
    """Tests for the task that archives contacts
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
        """Test that the task doesn't run if it cannot acquire the advisory_lock
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
        """Test contact archiving query limit
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
        """Test contact archiving simulate flag
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
        """Test that appropriate realtime messaging is sent which reflects the archiving actions
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
        """Test contact archiving with no updates on contacts
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
        """Test contact archiving with updates on correct contacts
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

    last_modfied = datetime.datetime.now()
    for file in test_files:
        # use freeze_time to allow uploaded files to have a different LastModified date
        with freeze_time(last_modfied):
            mock_s3_client.put_object(
                Bucket=bucket_name,
                Key=file,
                Body=json.dumps('Test contents'),
            )
            last_modfied = last_modfied + datetime.timedelta(seconds=3)


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
        """Test that the task doesn't run if it cannot acquire the advisory_lock
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
    FROZEN_TIME = datetime.datetime(2024, 6, 1, 2, tzinfo=timezone.utc)

    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_ingest_with_exception_logs_error_and_reraises_original_exception(self, test_files):
        """Test that the task can catch and log any unhandled exceptions
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
    def test_ingest_with_empty_s3_bucket_does_not_call_sync(self):
        """Test that the task can handle an empty S3 bucket
        """
        setup_s3_bucket(BUCKET, [])
        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            sync_file_with_database=mock.DEFAULT,
        ):
            task.ingest()
            task.sync_file_with_database.assert_not_called()

    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_ingest_with_newest_file_key_equal_to_existing_file_key_does_not_call_sync(
        self,
        test_files,
    ):
        """Test that the task returns when the latest file is equal to an existing ingested file
        """
        setup_s3_bucket(BUCKET, test_files)
        IngestedObjectFactory(object_key=test_files[-1])
        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            sync_file_with_database=mock.DEFAULT,
        ):
            task.ingest()
            task.sync_file_with_database.assert_not_called()

    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_ingest_calls_sync_with_newest_file_when_file_is_new(
        self,
        test_files,
    ):
        """Test that the ingest calls the sync with the latest file when the file key does
        not exist in the list of previously ingested files
        """
        setup_s3_bucket(BUCKET, test_files)
        IngestedObjectFactory()
        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            sync_file_with_database=mock.DEFAULT,
        ):
            task.ingest()
            task.sync_file_with_database.assert_called_once_with(
                mock.ANY,
                test_files[-1],
            )
            assert IngestedObject.objects.filter(object_key=test_files[-1]).exists()

    @mock_aws
    def test_sync_file_without_contacts_stops_job_processing(self):
        """Test when no contacts are found, the function doesn't continue
        """
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        assert (
            ContactConsentIngestionTask().sync_file_with_database(
                boto3.client('s3', REGION),
                filename,
            )
            is None
        )

    @mock_aws
    def test_sync_file_with_row_without_email_key(self):
        """Test when a row is processed that has no email key it is skipped
        """
        contact = ContactFactory()
        row = {'consents': 'A'}
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(row))
        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data is None

    @mock_aws
    def test_sync_file_with_row_with_email_key_that_is_blank(self):
        """Test when a row is processed that has no an email key that contains a blank string it
        is skipped
        """
        contact = ContactFactory()
        file_row = {'email': '', 'consents': 'A'}
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(file_row))
        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data is None

    @mock_aws
    def test_sync_file_with_row_without_consents_key(self):
        """Test when a row is processed that has no consents key it is skipped
        """
        contact = ContactFactory()
        file_row = {'email': contact.email}
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(file_row))
        ContactConsentIngestionTask().sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data is None

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    def test_sync_file_without_matching_email_does_not_update_contact(self):
        """Test when a row has an email that does not match a contact no changes are made
        """
        file_row = {
            'email': 'not_matching@bar.com',
            'consents': [{'consent_domain': 'Domestic', 'email_contact_consent': True}],
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(file_row))
        contact = ContactFactory(consent_data='A')

        task = ContactConsentIngestionTask()
        task.sync_file_with_database(boto3.client('s3', REGION), filename)
        assert Contact.objects.filter(id=contact.id).first().consent_data == 'A'
        assert Contact.objects.filter(email='not_matching@bar.com').first() is None

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    def test_sync_file_with_matching_email_without_loaded_contacts_does_not_update_contact(self):
        """Test when a row has an email that has a key in the contacts grouped dictionary, but not
        any contacts on the value, no changes are made
        """
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        contact = ContactFactory(consent_data='A')
        file_row = {
            'email': contact.email,
            'consents': [{'consent_domain': 'Domestic', 'email_contact_consent': True}],
        }
        upload_file_to_s3(BUCKET, filename, json.dumps(file_row))
        with mock.patch.object(
            ContactConsentIngestionTask,
            'get_grouped_contacts',
            return_value={contact.email: []},
        ):
            task = ContactConsentIngestionTask()
            task.sync_file_with_database(boto3.client('s3', REGION), filename)
            assert Contact.objects.filter(id=contact.id).first().consent_data == 'A'
            assert Contact.objects.filter(email='not_matching@bar.com').first() is None

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    def test_sync_file_with_matching_email_but_fails_contact_check_does_not_update_contact(
        self,
    ):
        """Test when a row has an email that matches a contact, but doesn't pass the check on
        whether the contact should be updated
        """
        contact = ContactFactory(
            consent_data='A',
        )
        file_row = {
            'email': contact.email,
            'consents': {'consent': True},
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(file_row))

        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            should_update_contact=mock.MagicMock(
                return_value=False,
            ),
        ):

            task.sync_file_with_database(boto3.client('s3', REGION), filename)
            assert Contact.objects.filter(id=contact.id).first().consent_data == 'A'

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    def test_sync_file_with_matching_email_and_passes_contact_check_does_update_contact(
        self,
    ):
        """Test when a row has an email that matches a contact, and passes the check on
        whether the contact should be updated, the contact is updated
        """
        contact = ContactFactory(consent_data='A', consent_data_last_modified=None)
        file_row = {
            'email': contact.email,
            'consents': {'consent': True},
            'last_modified': '2023-07-20T12:00:00',
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(file_row))

        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            should_update_contact=mock.MagicMock(
                return_value=True,
            ),
        ):

            task.sync_file_with_database(boto3.client('s3', REGION), filename)
            matching_contact = Contact.objects.filter(id=contact.id).first()
            assert matching_contact is not None
            assert matching_contact.consent_data == {'consent': True}
            assert matching_contact.consent_data_last_modified is not None

    @mock_aws
    @freeze_time(FROZEN_TIME)
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=True)
    def test_sync_file_with_multiple_contacts_matching_email_does_update_contact(self):
        """Test when a row has an email that matches multiple contacts all contacts are updated
        """
        test_email = 'duplicate@test.com'
        ContactFactory.create()
        ContactFactory.create_batch(
            3,
            email=test_email,
            consent_data='A',
            consent_data_last_modified='2023-07-20T12:00:00',
        )
        file_row = {
            'email': test_email,
            'last_modified': None,
            'consents': {'consent': True},
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(file_row))

        task = ContactConsentIngestionTask()

        task.sync_file_with_database(boto3.client('s3', REGION), filename)

        for contact in Contact.objects.filter(email=test_email):
            assert contact.consent_data == {'consent': True}
            assert contact.consent_data_last_modified == self.FROZEN_TIME

    @mock_aws
    @override_settings(ENABLE_CONTACT_CONSENT_INGEST=False)
    def test_sync_file_with_matching_email_but_ingest_setting_false_does_not_update_contact(self):
        """Test when a row has an email that matches a contact but the ENABLE_CONTACT_CONSENT_INGEST
        setting is false the contact is not updated
        """
        contact = ContactFactory(
            consent_data='A',
        )
        file_row = {
            'email': contact.email,
            'consents': {'consent': True},
        }
        filename = f'{CONSENT_PREFIX}file_{uuid.uuid4()}.jsonl'
        upload_file_to_s3(BUCKET, filename, json.dumps(file_row))

        task = ContactConsentIngestionTask()
        with mock.patch.multiple(
            task,
            should_update_contact=mock.MagicMock(
                return_value=True,
            ),
        ):

            task.sync_file_with_database(boto3.client('s3', REGION), filename)
            assert Contact.objects.filter(id=contact.id).first().consent_data == 'A'

    def test_get_grouped_contacts_returns_empty_dict_when_no_contacts(self):
        """Test when no contacts are present an empty dictionary is returned
        """
        assert ContactConsentIngestionTask().get_grouped_contacts() == {}

    def test_get_grouped_contacts_returns_unique_contacts_with_different_emails(self):
        """Test when contacts with a unique email are present, the dictionary returns 1 row per
        unique email with only the contacts matching that email as the value
        """
        contact1 = ContactFactory.create(email='unique1@test.com')
        contact2 = ContactFactory.create(email='unique2@test.com')
        assert ContactConsentIngestionTask().get_grouped_contacts() == {
            'unique1@test.com': [contact1],
            'unique2@test.com': [contact2],
        }

    def test_get_grouped_contacts_returns_grouped_contacts_with_same_email(self):
        """Test when contacts with a duplicate emails are present, the dictionary returns a row with
        the duplicate email as the key and all contacts matching that email as the value
        """
        contacts = ContactFactory.create_batch(3, email='grouped@test.com')
        grouped = ContactConsentIngestionTask().get_grouped_contacts()

        assert 'grouped@test.com' in grouped
        assert set(grouped['grouped@test.com']) == set(contacts)

    def test_should_update_contact_with_row_date_missing_should_return_true(
        self,
    ):
        """Test when a row has an email that matches a contact, but the file has missing date,
        returns True
        """
        task = ContactConsentIngestionTask()
        contact = ContactFactory.create(consent_data_last_modified=datetime.datetime.now())

        row = {
            'email': 'a',
            'last_modified': None,
            'consents': {'consent': True},
        }
        assert task.should_update_contact(
            contact,
            row,
        )

    def test_should_update_contact_with_contact_date_missing_should_return_true(
        self,
    ):
        """Test when a row has an email that matches a contact, but the contact has missing date,
        returns True
        """
        task = ContactConsentIngestionTask()
        contact = ContactFactory.create(consent_data_last_modified=None)
        row = {
            'email': 'a',
            'last_modified': '2023-07-20T12:00:00',
            'consents': {'consent': True},
        }

        assert task.should_update_contact(
            contact,
            row,
        )

    def test_should_update_contact_with_row_date_older_contact_date_should_return_false(
        self,
    ):
        """Test when a row has an email that matches a contact, but the file has an older modified
        date, returns False
        """
        task = ContactConsentIngestionTask()
        contact = ContactFactory.create(
            consent_data_last_modified=datetime.datetime.fromisoformat('2024-08-02T12:00:00'),
        )
        row = {
            'email': 'a',
            'last_modified': '2023-07-20T12:00:00',
            'consents': {'consent': True},
        }
        assert (
            task.should_update_contact(
                contact,
                row,
            )
            is False
        )

    def test_should_update_contact_with_row_date_newer_than_contact_date_should_return_true(
        self,
    ):
        """Test when a row has an email that matches a contact, but the file has an newer modified
        date, returns True
        """
        task = ContactConsentIngestionTask()
        contact = ContactFactory.create(
            consent_data_last_modified=datetime.datetime.fromisoformat('2023-07-20T12:00:00'),
        )
        row = {
            'email': 'a',
            'last_modified': '2024-08-02T12:00:00',
            'consents': {'consent': True},
        }
        assert task.should_update_contact(
            contact,
            row,
        )
