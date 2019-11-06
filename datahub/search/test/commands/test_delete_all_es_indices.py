from unittest.mock import Mock

import pytest
from django.core import management
from django.test import override_settings

from datahub.search.management.commands import delete_all_es_indices

CAT_INDICES_MOCK_DATA = [
    {
        'health': 'yellow',
        'status': 'open',
        'index': 'test-datahub-interaction-ec946a2e4301393aa5fdd9f109b60cf6',
        'uuid': 'i2Lm4K3kSOufk8Ev7YHtdg',
        'pri': '5',
        'rep': '1',
        'docs.count': '16703',
        'docs.deleted': '4472',
        'store.size': '32.3mb',
        'pri.store.size': '32.3mb',
    },
]


@override_settings(ES_INDEX_PREFIX='test-datahub')
@pytest.mark.parametrize('interactive', (True, False))
def test_deletes_matching_indices(mock_es_client, interactive, monkeypatch):
    """Test that indices matching the ES_INDEX_PREFIX prefix are deleted."""
    mocked_input = Mock(return_value='yes')
    monkeypatch.setattr('builtins.input', mocked_input)
    mock_es_client.return_value.cat.indices.return_value = CAT_INDICES_MOCK_DATA

    management.call_command(
        delete_all_es_indices.Command(),
        interactive=interactive,
    )

    mock_es_client.return_value.cat.indices.assert_called_once_with(
        index='test-datahub-*',
        format='json',
    )
    mock_es_client.return_value.indices.delete.assert_called_once_with(
        'test-datahub-interaction-ec946a2e4301393aa5fdd9f109b60cf6',
    )
    assert mocked_input.call_count == (1 if interactive else 0)


@override_settings(ES_INDEX_PREFIX='test-datahub')
def test_skips_deleting_if_no_matching_indices(mock_es_client):
    """Test that if no indices match, no attempt to delete indices is made."""
    mock_es_client.return_value.cat.indices.return_value = []

    management.call_command(delete_all_es_indices.Command())

    mock_es_client.return_value.indices.delete.assert_not_called()


def test_skips_deleting_if_not_confirmed(mock_es_client, monkeypatch):
    """
    Test that if the user types 'no' when asked to confirm the action, the command
    exits without deleting.
    """
    mocked_input = Mock(return_value='no')
    monkeypatch.setattr('builtins.input', mocked_input)
    mock_es_client.return_value.cat.indices.return_value = CAT_INDICES_MOCK_DATA

    management.call_command(delete_all_es_indices.Command(), interactive=True)

    mock_es_client.return_value.indices.delete.assert_not_called()
    mocked_input.assert_called()
