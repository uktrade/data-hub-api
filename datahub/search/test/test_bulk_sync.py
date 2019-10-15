from unittest.mock import Mock

import pytest

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import MockQuerySet
from datahub.search.bulk_sync import sync_app, sync_objects
from datahub.search.company import CompanySearchApp
from datahub.search.signals import disable_search_signal_receivers
from datahub.search.test.utils import create_mock_search_app


def test_sync_app_with_default_batch_size(monkeypatch):
    """Tests syncing an app to Elasticsearch with the default batch size."""
    bulk_mock = Mock()
    monkeypatch.setattr('datahub.search.bulk_sync.bulk', bulk_mock)

    search_app = create_mock_search_app(
        queryset=MockQuerySet([Mock(id=1), Mock(id=2)]),
    )
    sync_app(search_app)

    assert bulk_mock.call_count == 1


def test_sync_app_with_overridden_batch_size(monkeypatch):
    """Tests syncing an app to Elasticsearch with an overridden batch size."""
    bulk_mock = Mock()
    monkeypatch.setattr('datahub.search.bulk_sync.bulk', bulk_mock)

    search_app = create_mock_search_app(
        queryset=MockQuerySet([Mock(id=1), Mock(id=2)]),
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
        queryset=MockQuerySet([Mock(id=1), Mock(id=2)]),
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


@pytest.mark.django_db
@disable_search_signal_receivers(Company)
def test_sync_app_uses_latest_data(monkeypatch, es_with_signals):
    """Test that sync_app() picks up updates made to records between batches."""
    CompanyFactory.create_batch(2, name='old name')

    def sync_objects_side_effect(*args, **kwargs):
        nonlocal mock_sync_objects

        ret = sync_objects(*args, **kwargs)

        if mock_sync_objects.call_count == 1:
            Company.objects.update(name='new name')

        return ret

    mock_sync_objects = Mock(side_effect=sync_objects_side_effect)
    monkeypatch.setattr('datahub.search.bulk_sync.sync_objects', mock_sync_objects)
    sync_app(CompanySearchApp, batch_size=1)

    es_with_signals.indices.refresh()

    company = mock_sync_objects.call_args_list[1][0][1][0]
    fetched_company = es_with_signals.get(
        index=CompanySearchApp.es_model.get_read_alias(),
        doc_type=CompanySearchApp.name,
        id=company.pk,
    )
    assert fetched_company['_source']['name'] == 'new name'
