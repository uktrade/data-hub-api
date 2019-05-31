from unittest import mock

import pytest
from django.test.utils import override_settings

from datahub.email_ingestion.mailbox import MailboxHandler
from datahub.email_ingestion.tasks import ingest_emails
from datahub.email_ingestion.test.utils import MAILBOXES_SETTING, mock_import_string


class TestIngestEmails:
    """
    Test ingest_emails celery task.
    """

    @pytest.mark.django_db
    @override_settings(MAILBOXES=MAILBOXES_SETTING)
    def test_ingest_emails_lock_acquired(self, monkeypatch):
        """
        Test that our mailboxes are processed when the lock is acquired.
        """
        # Mock import_string to avoid import errors for processor_class path strings
        mock_import_string(monkeypatch)
        process_new_mail_patch = mock.Mock()
        # ensure that the process_new_mail method is a mock so we can interrogate later
        monkeypatch.setattr(
            'datahub.email_ingestion.mailbox.Mailbox.process_new_mail',
            process_new_mail_patch,
        )
        # Refresh the mailbox_handler singleton as we have overidden the MAILBOXES setting
        mailbox_handler = MailboxHandler()
        mailbox_handler.initialise_mailboxes()
        monkeypatch.setattr(
            'datahub.email_ingestion.tasks.mailbox_handler',
            mailbox_handler,
        )
        ingest_emails()
        assert process_new_mail_patch.call_count == 2

    @override_settings(MAILBOXES=MAILBOXES_SETTING)
    def test_ingest_emails_lock_not_acquired(self, monkeypatch):
        """
        Test that our mailboxes are not processed when the lock cannot be acquired successfully.
        """
        process_new_mail_patch = mock.Mock()
        # ensure that the process_new_mail method is a mock so we can interrogate later
        monkeypatch.setattr(
            'datahub.email_ingestion.mailbox.Mailbox.process_new_mail',
            process_new_mail_patch,
        )
        # Have to mock rather than acquire the lock as locks are per connection (if the lock is
        # already held by the current connection, the current connection can still re-acquire it).
        advisory_lock_mock = mock.MagicMock()
        advisory_lock_mock.return_value.__enter__.return_value = False
        monkeypatch.setattr('datahub.email_ingestion.tasks.advisory_lock', advisory_lock_mock)

        ingest_emails()
        assert process_new_mail_patch.called is False
