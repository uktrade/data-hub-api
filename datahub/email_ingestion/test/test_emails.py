from unittest import mock

import pytest
from django.test.utils import override_settings

from datahub.email_ingestion import emails
from datahub.email_ingestion.models import MailboxLogging, MailboxProcessingStatus
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction import MAILBOX_INGESTION_FEATURE_FLAG_NAME
from datahub.interaction.test.factories import CompanyInteractionFactory

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


@pytest.mark.django_db
class TestMailbox:
    """
    Test the mailbox module.
    """

    @override_settings(DOCUMENT_BUCKETS=DOCUMENT_BUCKETS_SETTING)
    def test_mailbox_process_ingestion_emails(self, monkeypatch):
        """
        Tests processing of emails.
        """
        mock_query = mock.Mock(return_value=DOCUMENTS)
        mock_delete = mock.Mock()
        interaction = CompanyInteractionFactory()
        mock_process = mock.Mock(return_value=(True, 'ok', interaction.id))
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
        log = MailboxLogging.objects.all()
        assert log.exists()
        assert log[0].source == DOCUMENTS[0]['source']
        assert log[0].content == DOCUMENTS[0]['content'].decode('utf-8')
        assert log[0].status == MailboxProcessingStatus.PROCESSED
        assert log[0].extra == 'ok'
        assert log[0].interaction_id == interaction.id

    @override_settings(DOCUMENT_BUCKETS=DOCUMENT_BUCKETS_SETTING)
    def test_mailbox_process_ingestion_emails_fails_processing(self, monkeypatch):
        """
        Tests processing of emails.
        """
        mock_query = mock.Mock(return_value=DOCUMENTS)
        mock_delete = mock.Mock()
        mock_process = mock.Mock(return_value=(False, 'some error', None))
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
        log = MailboxLogging.objects.all()
        assert log.exists()
        assert log[0].source == DOCUMENTS[0]['source']
        assert log[0].content == DOCUMENTS[0]['content'].decode('utf-8')
        assert log[0].status == MailboxProcessingStatus.FAILURE
        assert log[0].extra == 'some error'
        assert log[0].interaction is None

    @override_settings(DOCUMENT_BUCKETS=DOCUMENT_BUCKETS_SETTING)
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
        log = MailboxLogging.objects.all()
        assert log.exists()
        assert log[0].source == DOCUMENTS[0]['source']
        assert log[0].content == DOCUMENTS[0]['content'].decode('utf-8')
        assert log[0].status == MailboxProcessingStatus.FAILURE
        assert log[0].extra == 'Exception()'
        assert log[0].interaction is None
