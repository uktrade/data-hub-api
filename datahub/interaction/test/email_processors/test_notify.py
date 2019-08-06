from unittest.mock import Mock

import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.interaction.email_processors.notify import (
    get_domain_label,
    notify_meeting_ingest_failure,
    notify_meeting_ingest_success,
)


@pytest.fixture
def mock_statsd(monkeypatch):
    """
    Returns a mock statsd client instance.
    """
    mock_statsd = Mock()
    monkeypatch.setattr(
        'datahub.interaction.email_processors.notify.statsd',
        mock_statsd,
    )
    return mock_statsd


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
def test_notify_email_ingest_failure(mock_statsd):
    """
    Test that the `notify_email_ingest_failure` fucntion increments the
    right counters in StatsD.
    """
    adviser = AdviserFactory(contact_email='adviser@dit.gov.uk')
    notify_meeting_ingest_failure(adviser, (), ())
    mock_statsd.incr.assert_called_once_with(
        f'celery.calendar-invite-ingest.failure.dit_gov_uk',
    )


@pytest.mark.django_db
def test_notify_email_ingest_success(mock_statsd):
    """
    Test that the `notify_email_ingest_failure` fucntion increments the
    right counters in StatsD.
    """
    adviser = AdviserFactory(contact_email='adviser@dit.gov.uk')
    notify_meeting_ingest_success(adviser, Mock(), ())
    mock_statsd.incr.assert_called_once_with(
        f'celery.calendar-invite-ingest.success.dit_gov_uk',
    )
