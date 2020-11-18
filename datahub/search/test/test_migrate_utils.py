from unittest.mock import ANY, Mock

import pytest

from datahub.core.exceptions import DataHubException
from datahub.core.test_utils import MockQuerySet
from datahub.search.migrate_utils import (
    delete_from_secondary_indices_callback,
    resync_after_migrate,
)
from datahub.search.test.utils import create_mock_search_app


class TestResyncAfterMigrate:
    """Tests for resync_after_migrate()"""

    def test_normal_resync(self, monkeypatch, mock_es_client):
        """
        Test that resync_after_migrate() resyncs the app, updates the read alias and deletes the
        old index.
        """
        index_bulk_mock = Mock()
        delete_bulk_mock = Mock(return_value=(True, ({'delete': {'status': 404}},)))
        monkeypatch.setattr('datahub.search.bulk_sync.bulk', index_bulk_mock)
        monkeypatch.setattr('datahub.search.deletion.bulk', delete_bulk_mock)

        get_aliases_for_index_mock = Mock(return_value=set())
        monkeypatch.setattr(
            'datahub.search.migrate_utils.get_aliases_for_index',
            get_aliases_for_index_mock,
        )

        mock_client = mock_es_client.return_value
        read_indices = {'index1', 'index2'}
        write_index = 'index1'
        mock_app = create_mock_search_app(
            read_indices=read_indices,
            write_index=write_index,
            queryset=MockQuerySet([Mock(id=1), Mock(id=2)]),
        )

        resync_after_migrate(mock_app)

        assert index_bulk_mock.call_count == 1
        assert index_bulk_mock.call_args_list[0][1]['actions'] == [
            {
                '_index': 'index1',
                '_id': 1,
                '_type': 'test-type',
            },
            {
                '_index': 'index1',
                '_id': 2,
                '_type': 'test-type',
            },
        ]
        assert delete_bulk_mock.call_count == 1
        assert list(delete_bulk_mock.call_args_list[0][1]['actions']) == [
            {
                '_index': 'index2',
                '_id': 1,
                '_op_type': 'delete',
            },
            {
                '_index': 'index2',
                '_id': 2,
                '_op_type': 'delete',
            },
        ]

        mock_client.indices.update_aliases.assert_called_once()

        actions = mock_client.indices.update_aliases.call_args_list[0][1]['body']['actions']
        actions[0]['remove']['indices'] = sorted(actions[0]['remove']['indices'])

        mock_client.indices.update_aliases.assert_called_once_with(
            body={
                'actions': [
                    {
                        'remove': {
                            'alias': 'test-read-alias',
                            'indices': ANY,
                        },
                    },
                ],
            },
        )

        actions = mock_client.indices.update_aliases.call_args_list[0][1]['body']['actions']
        assert sorted(actions[0]['remove']['indices']) == ['index2']

        assert mock_client.indices.delete.call_count == 1
        mock_client.indices.delete.assert_any_call('index2')

    def test_resync_with_deletion_error(self, monkeypatch, mock_es_client):
        """
        Test that resync_after_migrate() raises an exception when there is an error deleting
        documents.
        """
        index_bulk_mock = Mock()
        delete_bulk_mock = Mock(return_value=(True, ({'delete': {'status': 500}},)))
        monkeypatch.setattr('datahub.search.bulk_sync.bulk', index_bulk_mock)
        monkeypatch.setattr('datahub.search.deletion.bulk', delete_bulk_mock)

        get_aliases_for_index_mock = Mock(return_value=set())
        monkeypatch.setattr(
            'datahub.search.migrate_utils.get_aliases_for_index',
            get_aliases_for_index_mock,
        )

        read_indices = {'index1', 'index2'}
        write_index = 'index1'
        mock_app = create_mock_search_app(
            read_indices=read_indices,
            write_index=write_index,
            queryset=MockQuerySet([Mock(id=1), Mock(id=2)]),
        )

        with pytest.raises(DataHubException):
            resync_after_migrate(mock_app)

    def test_resync_with_old_index_referenced(self, monkeypatch, mock_es_client):
        """
        Test that if the old index is still referenced, resync_after_migrate() does not delete it.
        """
        sync_app_mock = Mock()
        monkeypatch.setattr('datahub.search.migrate_utils.sync_app', sync_app_mock)

        get_aliases_for_index_mock = Mock(return_value={'another-index'})
        monkeypatch.setattr(
            'datahub.search.migrate_utils.get_aliases_for_index',
            get_aliases_for_index_mock,
        )

        mock_client = mock_es_client.return_value
        read_indices = {'index1', 'index2'}
        write_index = 'index1'
        mock_app = create_mock_search_app(
            read_indices=read_indices,
            write_index=write_index,
        )

        resync_after_migrate(mock_app)

        sync_app_mock.assert_called_once_with(
            mock_app,
            post_batch_callback=delete_from_secondary_indices_callback,
        )

        mock_client.indices.update_aliases.assert_called_once_with(
            body={
                'actions': [
                    {
                        'remove': {
                            'alias': 'test-read-alias',
                            'indices': ['index2'],
                        },
                    },
                ],
            },
        )

        mock_client.indices.delete.assert_not_called()

    def test_resync_with_single_read_index(self, monkeypatch, mock_es_client):
        """
        Test that the function aborts if the there is only a single read index.
        """
        sync_app_mock = Mock()
        monkeypatch.setattr('datahub.search.migrate_utils.sync_app', sync_app_mock)

        get_aliases_for_index_mock = Mock(return_value=set())
        monkeypatch.setattr(
            'datahub.search.migrate_utils.get_aliases_for_index',
            get_aliases_for_index_mock,
        )

        mock_client = mock_es_client.return_value
        read_indices = {'index1'}
        write_index = 'index1'
        mock_app = create_mock_search_app(
            read_indices=read_indices,
            write_index=write_index,
        )

        resync_after_migrate(mock_app)

        sync_app_mock.assert_not_called()

        mock_client.indices.update_aliases.assert_not_called()
        mock_client.indices.delete.assert_not_called()

    def test_resync_in_invalid_state(self, monkeypatch, mock_es_client):
        """
        Test that if the there is only a single read index, no aliases are updated and no indices
        are deleted.
        """
        sync_app_mock = Mock()
        monkeypatch.setattr('datahub.search.migrate_utils.sync_app', sync_app_mock)

        get_aliases_for_index_mock = Mock(return_value=set())
        monkeypatch.setattr(
            'datahub.search.migrate_utils.get_aliases_for_index',
            get_aliases_for_index_mock,
        )

        read_indices = {'index2', 'index3'}
        write_index = 'index1'
        mock_app = create_mock_search_app(
            read_indices=read_indices,
            write_index=write_index,
        )

        with pytest.raises(DataHubException):
            resync_after_migrate(mock_app)

        # The state is only checked once sync_app has run, as it's making sure nothing has
        # changed while sync_app was running
        sync_app_mock.assert_called_once_with(
            mock_app,
            post_batch_callback=delete_from_secondary_indices_callback,
        )
