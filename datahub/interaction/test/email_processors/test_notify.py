from unittest.mock import call, Mock

import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.interaction.email_processors.notify import (
    get_domain_label,
    notify_meeting_ingest_failure,
    notify_meeting_ingest_success,
)


@pytest.fixture
def mock_logger(monkeypatch):
    """
    Returns a mock logger client instance.
    """
    mock_logger = Mock()
    monkeypatch.setattr(
        'datahub.interaction.email_processors.notify.logger',
        mock_logger,
    )
    return mock_logger


@pytest.mark.parametrize(
    'domain, label',
    (
        ('dit.gov.uk', 'dit_gov_uk'),
    ),
)
def test_get_domain_label(domain, label):
    """
    Test if the `get_domain_label` function converts
    a given domain (with "." characters) to a Prometheus
    label (without "." characters).
    """
    assert get_domain_label(domain) == label


@pytest.mark.django_db
def test_notify_email_ingest_failure(mock_logger):
    """
    Test that the `notify_email_ingest_failure` logs failures
    """
    adviser = AdviserFactory(contact_email='adviser@dit.gov.uk')
    notify_meeting_ingest_failure(adviser, (), ())
    calls = [
        call('rq.calendar-invite-ingest.failure.dit_gov_uk'),
        call('Feature flag "mailbox-notification" is not active, exiting.'),
    ]
    mock_logger.info.assert_has_calls(calls)


@pytest.mark.django_db
def test_notify_email_ingest_success(mock_logger):
    """
    Test that the `notify_email_ingest_success` logs success
    """
    adviser = AdviserFactory(contact_email='adviser@dit.gov.uk')
    notify_meeting_ingest_success(adviser, Mock(), ())
    calls = [
        call('rq.calendar-invite-ingest.success.dit_gov_uk'),
        call('Feature flag "mailbox-notification" is not active, exiting.'),
    ]
    mock_logger.info.assert_has_calls(calls)
