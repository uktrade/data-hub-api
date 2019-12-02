from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def mock_get_company_updates(monkeypatch):
    """
    Test fixture to mock get_company_updates celery task.
    """
    mocked_get_company_updates = mock.Mock()
    monkeypatch.setattr(
        'datahub.dnb_api.management.commands.update_companies_from_dnb_service'
        '.get_company_updates',
        mocked_get_company_updates,
    )
    return mocked_get_company_updates


def test_no_argument_raises_command_error(mock_get_company_updates):
    """
    Test update_companies_from_dnb_service command with no arguments raises a
    CommandError.
    """
    with pytest.raises(CommandError) as excinfo:
        call_command('update_companies_from_dnb_service')
    expected_message = 'Error: the following arguments are required: last_updated_after'
    assert str(excinfo.value) == expected_message
    assert mock_get_company_updates.call_count == 0


def test_update_all_fields(mock_get_company_updates):
    """
    Test update_companies_from_dnb_service command with no options calls through to
    get_company_updates celery task successfully.
    """
    datetime = '2019-01-01T00:00:00'
    call_command(
        'update_companies_from_dnb_service',
        datetime,
    )
    mock_get_company_updates.apply.assert_called_with(kwargs={
        'last_updated_after': datetime,
        'fields_to_update': None,
    })


def test_update_partial_fields(mock_get_company_updates):
    """
    Test update_companies_from_dnb_service command with a --fields option calls through to
    get_company_updates celery task successfully.
    """
    datetime = '2019-01-01T00:00:00'
    fields = ['name']
    call_command(
        'update_companies_from_dnb_service',
        datetime,
        fields=fields,
    )
    mock_get_company_updates.apply.assert_called_with(kwargs={
        'last_updated_after': datetime,
        'fields_to_update': fields,
    })
