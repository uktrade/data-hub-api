from unittest import mock

import pytest
from django.core.cache import cache
from django.test.utils import override_settings

from datahub.email_ingestion.mailbox import EmailInboxConnectionError, MailboxHandler
from datahub.email_ingestion.tasks import ingest_emails
from datahub.email_ingestion.test.utils import MAILBOXES_SETTING, mock_import_string
from datahub.feature_flag.models import FeatureFlag
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction import INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME


@pytest.fixture()
def interaction_email_ingestion_feature_flag():
    """
    Creates the email ingestion feature flag.
    """
    yield FeatureFlagFactory(code=INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME)


@pytest.mark.django_db
@pytest.mark.usefixtures('interaction_email_ingestion_feature_flag')
class TestIngestEmails:
    """
    Test ingest_emails celery task.
    """

    def _refresh_mailbox_handler(self, monkeypatch):
        mailbox_handler = MailboxHandler()
        mailbox_handler.initialise_mailboxes()
        monkeypatch.setattr(
            'datahub.email_ingestion.tasks.mailbox_handler',
            mailbox_handler,
        )

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
        self._refresh_mailbox_handler(monkeypatch)

        ingest_emails()
        assert process_new_mail_patch.call_count == 2

    @pytest.mark.usefixtures('local_memory_cache')
    @override_settings(
        MAILBOXES=MAILBOXES_SETTING,
        EMAIL_INGESTION_CONNECT_FAILURE_THRESHOLD=5,
    )
    def test_ingest_emails_repeated_failures(self, monkeypatch):
        """
        Test that repeated failures of the ingest_emails task will only yield
        one error within a sufficient window.
        """
        # Mock import_string to avoid import errors for processor_class path strings
        mock_import_string(monkeypatch)

        # The process_new_mail call for our test inbox should pass or fail according to
        # this manifest
        call_results = [True, False, True, False, False, False, False]

        def failing_connect(self, *args, **kwargs):
            if self.username == 'mybox2@example.net':
                try:
                    self.call_count
                except AttributeError:
                    self.call_count = 0
                result = call_results[self.call_count]
                self.call_count += 1
                if not result:
                    raise EmailInboxConnectionError('Connection error')

        monkeypatch.setattr(
            'datahub.email_ingestion.mailbox.Mailbox.process_new_mail',
            failing_connect,
        )
        self._refresh_mailbox_handler(monkeypatch)

        # Simulate calling the ingest emails task a few times before we reach
        # the failure threshold
        for _i in call_results[:-1]:
            ingest_emails()

        assert cache.get('email_ingest_failures_mybox2@example.net') == 4
        # Call ingest_emails the final time - which should raise an error
        with pytest.raises(EmailInboxConnectionError):
            ingest_emails()
        # Ensure that the failure cache is cleared
        assert cache.get('email_ingest_failures_mybox2@example.net') is None

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

    def test_ingest_feature_flag_inactive(self, monkeypatch):
        """
        Test that our mailboxes are not processed when the feature flag is not active.
        """
        process_new_mail_patch = mock.Mock()
        # ensure that the process_new_mail method is a mock so we can interrogate later
        monkeypatch.setattr(
            'datahub.email_ingestion.mailbox.Mailbox.process_new_mail',
            process_new_mail_patch,
        )
        flag = FeatureFlag.objects.get(code=INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME)
        flag.is_active = False
        flag.save()

        ingest_emails()
        assert process_new_mail_patch.called is False
