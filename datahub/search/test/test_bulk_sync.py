from unittest.mock import Mock

import pytest

from datahub.core.test_utils import MockQuerySet
from datahub.search.bulk_sync import sync_app
from datahub.search.test.utils import create_mock_search_app

pytestmark = pytest.mark.django_db


def test_sync_app_with_default_batch_size(monkeypatch):
    """Tests syncing an app to Elasticsearch with the default batch size."""
    bulk_mock = Mock()
    monkeypatch.setattr('datahub.search.bulk_sync.bulk', bulk_mock)

    search_app = create_mock_search_app(
        queryset=MockQuerySet([Mock(id=1), Mock(id=2)])
    )
    sync_app(search_app)

    assert bulk_mock.call_count == 1


def test_sync_app_with_overridden_batch_size(monkeypatch):
    """Tests syncing an app to Elasticsearch with an overridden batch size."""
    bulk_mock = Mock()
    monkeypatch.setattr('datahub.search.bulk_sync.bulk', bulk_mock)

    search_app = create_mock_search_app(
        queryset=MockQuerySet([Mock(id=1), Mock(id=2)])
    )
    sync_app(search_app, batch_size=1)

    assert bulk_mock.call_count == 2


def test_sync_app_logic(monkeypatch):
    """Tests syncing an app to Elasticsearch during a mapping migration."""
    bulk_mock = Mock()
    monkeypatch.setattr('datahub.search.bulk_sync.bulk', bulk_mock)
    search_app = create_mock_search_app(
        current_mapping_hash='mapping-hash',
        target_mapping_hash='mapping-hash',
        read_indices=('index1', 'index2'),
        write_index='index1',
        queryset=MockQuerySet([Mock(id=1), Mock(id=2)])
    )
    sync_app(search_app, batch_size=1000)
    assert bulk_mock.call_args_list[0][1]['actions'] == [
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
    assert bulk_mock.call_count == 1
