from unittest import mock

import pytest

from datahub.email_ingestion.tasks import process_mailbox_emails
from datahub.feature_flag.models import FeatureFlag
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction import MAILBOX_INGESTION_FEATURE_FLAG_NAME


@pytest.fixture()
def mailbox_ingestion_feature_flag():
    """
    Creates the email ingestion feature flag.
    """
    yield FeatureFlagFactory(code=MAILBOX_INGESTION_FEATURE_FLAG_NAME)


@pytest.mark.django_db
@pytest.mark.usefixtures('mailbox_ingestion_feature_flag')
class TestIngestEmails:
    """
    Test ingest_emails RQ task.
    """

    def test_ingest_emails_lock_acquired(self, monkeypatch):
        """
        Test that our emails are processed when the lock is acquired.
        """
        process_emails_patch = mock.Mock()
        monkeypatch.setattr(
            'datahub.email_ingestion.emails.process_ingestion_emails',
            process_emails_patch,
        )
        process_mailbox_emails()
        assert process_emails_patch.call_count == 1

    def test_ingest_emails_lock_not_acquired(self, monkeypatch):
        """
        Test that our emails are not processed when the lock cannot be acquired successfully.
        """
        process_emails_patch = mock.Mock()
        monkeypatch.setattr(
            'datahub.email_ingestion.emails.process_ingestion_emails',
            process_emails_patch,
        )
        advisory_lock_mock = mock.MagicMock()
        advisory_lock_mock.return_value.__enter__.return_value = False
        monkeypatch.setattr('datahub.email_ingestion.tasks.advisory_lock', advisory_lock_mock)

        process_mailbox_emails()
        assert process_emails_patch.called is False

    def test_ingest_feature_flag_inactive(self, monkeypatch):
        """
        Test that our emails are not processed when the feature flag is not active.
        """
        process_emails_patch = mock.Mock()
        # ensure that the process_ingestion_emails method is a mock so we can interrogate later
        monkeypatch.setattr(
            'datahub.email_ingestion.emails.process_ingestion_emails',
            process_emails_patch,
        )
        flag = FeatureFlag.objects.get(code=MAILBOX_INGESTION_FEATURE_FLAG_NAME)
        flag.is_active = False
        flag.save()

        process_mailbox_emails()
        assert process_emails_patch.called is False
