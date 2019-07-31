from unittest.mock import Mock

import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.monitoring.interactions.email_processors import (
    get_adviser_domain,
    record_failure,
    record_success,
)


@pytest.fixture
def mock_failure_counter(monkeypatch):
    """
    Mocks the failure_counter.
    """
    mock_failure_counter = Mock()
    monkeypatch.setattr(
        'datahub.monitoring.interactions.email_processors.failure_counter',
        mock_failure_counter,
    )
    return mock_failure_counter


@pytest.fixture
def mock_success_counter(monkeypatch):
    """
    Mocks the success_counter.
    """
    mock_success_counter = Mock()
    monkeypatch.setattr(
        'datahub.monitoring.interactions.email_processors.success_counter',
        mock_success_counter,
    )
    return mock_success_counter


@pytest.fixture
def mock_push_to_gateway(monkeypatch):
    """
    Mocks push_to_gateway.
    """
    mock_push_to_gateway = Mock()
    monkeypatch.setattr(
        'datahub.monitoring.interactions.email_processors.push_to_gateway',
        mock_push_to_gateway,
    )
    return mock_push_to_gateway


@pytest.mark.parametrize(
    'email, domain',
    (
        ('adviser@dit.gov.uk', 'dit.gov.uk'),
        # TODO: Exotic test cases?
    ),
)
def test_get_adviser_domain(email, domain, db):
    """
    Test that given an email, the get_adviser_domain function
    returns the right domain.
    """
    adviser = AdviserFactory(email=email, contact_email=email)
    assert get_adviser_domain(adviser) == domain


def test_record_failure(mock_failure_counter, mock_push_to_gateway, db):
    """
    Test that the record_failure function increments the failure_counter
    and push the metric to the gateway.
    """
    email = 'adviser@dit.gov.uk'
    adviser = AdviserFactory(email=email, contact_email=email)
    record_failure(adviser)
    mock_failure_counter.labels.assert_called_once_with(
        domain='dit.gov.uk',
    )
    mock_failure_counter.labels.return_value.inc.assert_called_once_with()
    mock_push_to_gateway.assert_called_once_with('calendar-invite-ingest')


def test_record_success(mock_success_counter, mock_push_to_gateway, db):
    """
    Test that the record_success_counter function increments the success_counter
    and push the metric to the gateway.
    """
    email = 'adviser@dit.gov.uk'
    adviser = AdviserFactory(email=email, contact_email=email)
    record_success(adviser)
    mock_success_counter.labels.assert_called_once_with(
        domain='dit.gov.uk',
    )
    mock_success_counter.labels.return_value.inc.assert_called_once_with()
    mock_push_to_gateway.assert_called_once_with('calendar-invite-ingest')
