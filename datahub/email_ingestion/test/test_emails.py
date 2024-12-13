from unittest import mock

import pytest
from django.conf import settings
from django.test import override_settings
from rest_framework import status

from datahub.email_ingestion import emails
from datahub.email_ingestion.models import MailboxLogging, MailboxProcessingStatus
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction import MAILBOX_INGESTION_FEATURE_FLAG_NAME
from datahub.interaction.test.factories import CompanyInteractionFactory

MESSAGES = [{'id': 'key'}]
CONTENT = 'aaaaaaa'
TOKEN = 'token'


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

    @override_settings(
        MAILBOX_INGESTION_TENANT_ID='tenant',
        MAILBOX_INGESTION_EMAIL='test@email',
    )
    def test_mailbox_process_ingestion_emails(self, requests_mock, monkeypatch):
        """
        Tests processing of emails.
        """
        tenant_id = settings.MAILBOX_INGESTION_TENANT_ID
        token_mock = requests_mock.post(
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            json={'access_token': TOKEN},
            status_code=status.HTTP_200_OK,
        )
        email = settings.MAILBOX_INGESTION_EMAIL
        base_url = f'{settings.MAILBOX_INGESTION_GRAPH_URL}users/{email}'
        messages_mock = requests_mock.get(
            f'{base_url}/mailFolders/Inbox/messages',
            json={'value': MESSAGES},
            status_code=status.HTTP_200_OK,
        )
        content_mock = requests_mock.get(
            f'{base_url}/messages/key/$value',
            text=CONTENT,
            status_code=status.HTTP_200_OK,
        )
        delete_url = f'{base_url}/mailFolders/Inbox/messages/key'
        delete_mock = requests_mock.delete(
            delete_url,
            status_code=status.HTTP_204_NO_CONTENT,
        )
        interaction = CompanyInteractionFactory()
        mock_process = mock.Mock(return_value=(True, 'ok', interaction.id))

        monkeypatch.setattr(
            'datahub.interaction.email_processors.processors.'
            'InteractionPlainEmailProcessor.process_email',
            mock_process,
        )

        emails.process_ingestion_emails()
        assert mock_process.call_count == 1

        assert messages_mock.called_once
        assert delete_mock.called_once
        assert content_mock.called_once
        assert token_mock.called_once

        log = MailboxLogging.objects.all()
        assert log.exists()
        assert log[0].source == MESSAGES[0]['id']
        assert log[0].content == CONTENT
        assert log[0].status == MailboxProcessingStatus.PROCESSED
        assert log[0].extra == 'ok'
        assert log[0].interaction_id == interaction.id

    def test_mailbox_process_ingestion_emails_fails_processing(self, monkeypatch):
        """
        Tests processing of emails.
        """
        mock_token = mock.Mock(return_value=TOKEN)
        mock_query = mock.Mock(return_value=MESSAGES)
        mock_content = mock.Mock(return_value=CONTENT)
        mock_delete = mock.Mock()
        mock_process = mock.Mock(return_value=(False, 'some error', None))
        monkeypatch.setattr('datahub.email_ingestion.emails.get_access_token', mock_token)
        monkeypatch.setattr('datahub.email_ingestion.emails.read_messages', mock_query)
        monkeypatch.setattr('datahub.email_ingestion.emails.fetch_message', mock_content)
        monkeypatch.setattr('datahub.email_ingestion.emails.delete_message', mock_delete)
        monkeypatch.setattr(
            'datahub.interaction.email_processors.processors.'
            'InteractionPlainEmailProcessor.process_email',
            mock_process,
        )

        emails.process_ingestion_emails()
        assert mock_query.call_count == 1
        assert mock_process.call_count == 1
        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(
            TOKEN,
            MESSAGES[0]['id'],
        )
        log = MailboxLogging.objects.all()
        assert log.exists()
        assert log[0].source == MESSAGES[0]['id']
        assert log[0].content == CONTENT
        assert log[0].status == MailboxProcessingStatus.FAILURE
        assert log[0].extra == 'some error'
        assert log[0].interaction is None

    def test_mailbox_process_ingestion_emails_exception_when_processing(self, monkeypatch):
        """
        Tests processing of emails when exception happens.
        """
        mock_token = mock.Mock(return_value=TOKEN)
        mock_query = mock.Mock(return_value=MESSAGES)
        mock_content = mock.Mock(return_value=CONTENT)
        mock_delete = mock.Mock()
        mock_process = mock.Mock(side_effect=Exception())
        monkeypatch.setattr('datahub.email_ingestion.emails.get_access_token', mock_token)
        monkeypatch.setattr('datahub.email_ingestion.emails.read_messages', mock_query)
        monkeypatch.setattr('datahub.email_ingestion.emails.fetch_message', mock_content)
        monkeypatch.setattr('datahub.email_ingestion.emails.delete_message', mock_delete)
        monkeypatch.setattr(
            'datahub.interaction.email_processors.processors.'
            'InteractionPlainEmailProcessor.process_email',
            mock_process,
        )

        emails.process_ingestion_emails()
        assert mock_query.call_count == 1
        assert mock_process.call_count == 1
        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(
            TOKEN,
            MESSAGES[0]['id'],
        )
        log = MailboxLogging.objects.all()
        assert log.exists()
        assert log[0].source == MESSAGES[0]['id']
        assert log[0].content == CONTENT
        assert log[0].status == MailboxProcessingStatus.FAILURE
        assert log[0].extra == 'Exception()'
        assert log[0].interaction is None

    @override_settings(
        MAILBOX_INGESTION_TENANT_ID='tenant',
        MAILBOX_INGESTION_EMAIL='test@email',
    )
    def test_mailbox_process_ingestion_emails_not_processed_when_delete_fails(
        self,
        requests_mock,
        monkeypatch,
        caplog,
    ):
        """
        Tests processing of emails when delete fails.
        """
        caplog.set_level('ERROR')
        tenant_id = settings.MAILBOX_INGESTION_TENANT_ID
        token_mock = requests_mock.post(
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            json={'access_token': TOKEN},
            status_code=status.HTTP_200_OK,
        )
        email = settings.MAILBOX_INGESTION_EMAIL
        base_url = f'{settings.MAILBOX_INGESTION_GRAPH_URL}users/{email}'
        messages_mock = requests_mock.get(
            f'{base_url}/mailFolders/Inbox/messages',
            json={'value': MESSAGES},
            status_code=status.HTTP_200_OK,
        )
        content_mock = requests_mock.get(
            f'{base_url}/messages/key/$value',
            text=CONTENT,
            status_code=status.HTTP_200_OK,
        )
        delete_url = f'{base_url}/mailFolders/Inbox/messages/key'
        delete_mock = requests_mock.delete(
            delete_url,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        mock_process = mock.Mock(return_value=(True, 'ok'))
        monkeypatch.setattr(
            'datahub.interaction.email_processors.processors.'
            'InteractionPlainEmailProcessor.process_email',
            mock_process,
        )

        emails.process_ingestion_emails()
        assert messages_mock.called_once
        assert delete_mock.called_once
        assert content_mock.called_once
        assert token_mock.called_once
        mock_process.assert_not_called

        log = MailboxLogging.objects.all()
        assert not log.exists()

        assert f'Error deleting message: "{MESSAGES[0]["id"]}"' in caplog.text

    @override_settings(
        MAILBOX_INGESTION_TENANT_ID='tenant',
        MAILBOX_INGESTION_EMAIL='test@email',
    )
    def test_mailbox_process_ingestion_emails_no_message(self, requests_mock, monkeypatch, caplog):
        """
        Tests processing of emails and fail to fetch message.
        """
        tenant_id = settings.MAILBOX_INGESTION_TENANT_ID
        token_mock = requests_mock.post(
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            json={'access_token': TOKEN},
            status_code=status.HTTP_200_OK,
        )
        email = settings.MAILBOX_INGESTION_EMAIL
        base_url = f'{settings.MAILBOX_INGESTION_GRAPH_URL}users/{email}'
        messages_mock = requests_mock.get(
            f'{base_url}/mailFolders/Inbox/messages',
            json={'value': MESSAGES},
            status_code=status.HTTP_200_OK,
        )
        content_mock = requests_mock.get(
            f'{base_url}/messages/key/$value',
            text=CONTENT,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        delete_url = f'{base_url}/mailFolders/Inbox/messages/key'
        delete_mock = requests_mock.delete(
            delete_url,
            status_code=status.HTTP_204_NO_CONTENT,
        )
        interaction = CompanyInteractionFactory()
        mock_process = mock.Mock(return_value=(True, 'ok', interaction.id))

        monkeypatch.setattr(
            'datahub.interaction.email_processors.processors.'
            'InteractionPlainEmailProcessor.process_email',
            mock_process,
        )

        emails.process_ingestion_emails()
        mock_process.assert_not_called

        assert messages_mock.called_once
        assert delete_mock.call_count == 0
        assert content_mock.called_once
        assert token_mock.called_once

        log = MailboxLogging.objects.all()
        assert not log.exists()

        assert f'Error fetching message: "{MESSAGES[0]["id"]}"' in caplog.text
