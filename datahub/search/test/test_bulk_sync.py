from unittest.mock import Mock, patch

import pytest

from datahub.company.models import Advisor, Company
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import MockQuerySet
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import InteractionFactoryBase
from datahub.search.bulk_sync import sync_app, sync_objects
from datahub.search.company import CompanySearchApp
from datahub.search.adviser import AdviserSearchApp
from datahub.search.interaction import InteractionSearchApp
from datahub.search.signals import disable_search_signal_receivers
from datahub.search.test.utils import create_mock_search_app


def test_sync_app_with_default_batch_size(monkeypatch):
    """Tests syncing an app to OpenSearch with the default batch size."""
    bulk_mock = Mock()
    monkeypatch.setattr('datahub.search.bulk_sync.bulk', bulk_mock)

    search_app = create_mock_search_app(
        queryset=MockQuerySet([Mock(id=1), Mock(id=2)]),
    )
    sync_app(search_app)

    assert bulk_mock.call_count == 1


def test_sync_app_with_overridden_batch_size(monkeypatch):
    """Tests syncing an app to OpenSearch with an overridden batch size."""
    bulk_mock = Mock()
    monkeypatch.setattr('datahub.search.bulk_sync.bulk', bulk_mock)

    search_app = create_mock_search_app(
        queryset=MockQuerySet([Mock(id=1), Mock(id=2)]),
    )
    sync_app(search_app, batch_size=1)

    assert bulk_mock.call_count == 2


def test_sync_app_logic(monkeypatch):
    """Tests syncing an app to OpenSearch during a mapping migration."""
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
def test_sync_app_uses_latest_data(monkeypatch, opensearch):
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

    opensearch.indices.refresh()

    company = mock_sync_objects.call_args_list[1][0][1][0]
    fetched_company = opensearch.get(
        index=CompanySearchApp.search_model.get_read_alias(),
        id=company.pk,
    )
    assert fetched_company['_source']['name'] == 'new name'

@pytest.mark.django_db
@patch("datahub.search.bulk_sync.PROGRESS_INTERVAL", 1)
@disable_search_signal_receivers(Interaction)
def test_sync_app_log_messages__logs__modified_on(caplog):
    """Test with model with modified_on (interaction)."""
    interactions = InteractionFactoryBase.create_batch(2)

    caplog.set_level('INFO')

    sync_app(InteractionSearchApp, batch_size=1)

    # Assert 'modified_on' is shown for fields which have it.
    assert 'Processing Interaction records, using batch size 1' in caplog.text
    assert f'Interaction rows processed: 1/2 50% modified_on: {interactions[1].modified_on}' in caplog.text
    assert f'Interaction rows processed: 2/2 100% modified_on: {interactions[0].modified_on}' in caplog.text

@pytest.mark.django_db
@patch("datahub.search.bulk_sync.PROGRESS_INTERVAL", 1)
@disable_search_signal_receivers(Advisor)
def test_sync_app_log_messages__does_not_log__modified_on(caplog):
    """Test with model without modified_on field (adviser)."""
    AdviserFactory.create_batch(2)

    caplog.set_level('INFO')

    sync_app(AdviserSearchApp, batch_size=1)

    # Assert 'modified_on' is NOT shown for fields which don't have it.
    assert 'Processing Adviser records, using batch size 1' in caplog.text
    assert 'Adviser rows processed: 1/2 50%'
    assert f'modified_on:' not in caplog.text
    assert 'Adviser rows processed: 2/2 100%'
