from unittest import mock

import pytest
from django.test.utils import override_settings

from datahub.email_ingestion import emails
from datahub.email_ingestion.tasks import process_mailbox_emails
from datahub.feature_flag.models import FeatureFlag
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction import MAILBOX_INGESTION_FEATURE_FLAG_NAME

DOCUMENTS = [{'source': 'key', 'content': 'aaaaaaa'.encode()}]
DOCUMENT_BUCKETS_SETTING = {
    'mailbox': {
        'bucket': 'BUCKET',
        'aws_access_key_id': 'AWS-ACCESS-KEY-ID',
        'aws_secret_access_key': 'AWS-SECRET-ACCESS-KEY',
        'aws_region': 'AWS-REGION',
    },
}


@pytest.fixture()
def mailbox_ingestion_feature_flag():
    """
    Creates the email ingestion feature flag.
    """
    yield FeatureFlagFactory(code=MAILBOX_INGESTION_FEATURE_FLAG_NAME)


class TestMailbox:
    """
    Test the mailbox module.
    """

    @override_settings(MAILBOXES=DOCUMENT_BUCKETS_SETTING)
    def test_mailbox_process_ingestion_emails(self, monkeypatch):
        """
        Tests processing of emails.
        """
        mock_query = mock.Mock(return_value=DOCUMENTS)
        mock_delete = mock.Mock()
        mock_process = mock.Mock()
        monkeypatch.setattr('datahub.email_ingestion.emails.get_mail_docs_in_bucket', mock_query)
        monkeypatch.setattr('datahub.documents.utils.delete_document', mock_delete)
        monkeypatch.setattr(
            'datahub.interaction.email_processors.processors.'
            'CalendarInteractionEmailProcessor.process_email',
            mock_process,
        )

        emails.process_ingestion_emails()
        assert mock_query.call_count == 1
        assert mock_process.call_count == 1
        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(
            bucket_id=emails.BUCKET_ID, document_key=DOCUMENTS[0]['source'],
        )

    @override_settings(MAILBOXES=DOCUMENT_BUCKETS_SETTING)
    def test_mailbox_process_ingestion_emails_not_processed_with_deleted_docs(self, monkeypatch):
        """
        Tests processing of emails with error and deleted documents.
        """
        mock_query = mock.Mock(return_value=DOCUMENTS)
        mock_delete = mock.Mock()
        mock_process = mock.Mock()
        mock_process.side_effect = Exception()
        monkeypatch.setattr('datahub.email_ingestion.emails.get_mail_docs_in_bucket', mock_query)
        monkeypatch.setattr('datahub.documents.utils.delete_document', mock_delete)
        monkeypatch.setattr(
            'datahub.interaction.email_processors.processors.'
            'CalendarInteractionEmailProcessor.process_email',
            mock_process,
        )

        emails.process_ingestion_emails()
        assert mock_query.call_count == 1
        assert mock_process.call_count == 1
        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(
            bucket_id=emails.BUCKET_ID, document_key=DOCUMENTS[0]['source'],
        )


@pytest.mark.django_db
@pytest.mark.usefixtures('mailbox_ingestion_feature_flag')
class TestTasks:
    """
    Test celery task.
    """

    @override_settings(MAILBOXES=DOCUMENT_BUCKETS_SETTING)
    def test_process_mailbox_emails_lock_acquired(self, monkeypatch):
        """
        Test that mailbox is processed when the lock is acquired.
        """
        mocked = mock.Mock()
        monkeypatch.setattr('datahub.email_ingestion.emails.process_ingestion_emails', mocked)
        process_mailbox_emails()
        assert mocked.call_count == 1

    @override_settings(MAILBOXES=DOCUMENT_BUCKETS_SETTING)
    def test_process_mailbox_emails_lock_not_acquired(self, monkeypatch):
        """
        Test that mailbox is not processed when the lock is not acquired.
        """
        advisory_lock_mock = mock.MagicMock()
        advisory_lock_mock.return_value.__enter__.return_value = False
        monkeypatch.setattr('datahub.email_ingestion.tasks.advisory_lock', advisory_lock_mock)

        mocked = mock.Mock()
        monkeypatch.setattr('datahub.email_ingestion.emails.process_ingestion_emails', mocked)
        process_mailbox_emails()
        assert mocked.called is False
        assert mocked.call_count == 0

    @override_settings(MAILBOXES=DOCUMENT_BUCKETS_SETTING)
    def test_process_mailbox_emails_feature_flag_active(self, monkeypatch):
        """
        Test that mailbox is processed when the feature flag is active.
        """
        mocked = mock.Mock()
        monkeypatch.setattr('datahub.email_ingestion.emails.process_ingestion_emails', mocked)
        flag = FeatureFlag.objects.get(code=MAILBOX_INGESTION_FEATURE_FLAG_NAME)
        flag.is_active = True
        flag.save()
        process_mailbox_emails()
        assert mocked.call_count == 1

    @override_settings(MAILBOXES=DOCUMENT_BUCKETS_SETTING)
    def test_process_mailbox_emails_feature_flag_inactive(self, monkeypatch):
        """
        Test that mailbox is processed when the feature flag is not active.
        """
        mocked = mock.Mock()
        monkeypatch.setattr('datahub.email_ingestion.emails.process_ingestion_emails', mocked)
        flag = FeatureFlag.objects.get(code=MAILBOX_INGESTION_FEATURE_FLAG_NAME)
        flag.is_active = False
        flag.save()
        process_mailbox_emails()
        assert mocked.call_count == 0
