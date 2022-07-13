from unittest import mock

import pytest
from django.conf import settings
from django.db.models.signals import post_delete, pre_delete

from datahub.core.exceptions import DataHubError
from datahub.core.queues.queue import DataHubQueue
from datahub.search.deletion import (
    BULK_CHUNK_SIZE,
    BULK_DELETION_TIMEOUT_SECS,
    Collector,
    delete_documents,
    update_opensearch_after_deletions,
)
from datahub.search.sync_object import sync_object
from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.search.test.search_support.simplemodel.models import SearchSimpleModel


@mock.patch('datahub.search.opensearch.opensearch_bulk')
def test_delete_documents(opensearch_bulk, mock_opensearch_client):
    """Test that delete_documents calls OpenSearch bulk to delete all documents."""
    opensearch_bulk.return_value = (None, [])

    index = 'test-index'
    docs = [
        {'_id': 1},
        {'_id': 2},
        {'_id': 3},
    ]
    delete_documents(index, docs)

    assert opensearch_bulk.call_count == 1

    call_args, call_kwargs = opensearch_bulk.call_args_list[0]
    call_kwargs['actions'] = list(call_kwargs['actions'])  # from generator to list
    assert call_args == (mock_opensearch_client.return_value,)
    assert call_kwargs == {
        'actions': [
            {'_op_type': 'delete', '_index': index, **doc}
            for doc in docs
        ],
        'chunk_size': BULK_CHUNK_SIZE,
        'request_timeout': BULK_DELETION_TIMEOUT_SECS,
        'max_chunk_bytes': settings.OPENSEARCH_BULK_MAX_CHUNK_BYTES,
        'raise_on_error': False,
    }


@mock.patch('datahub.search.opensearch.opensearch_bulk')
def test_delete_documents_with_errors(opensearch_bulk, mock_opensearch_client):
    """Test that if OpenSearch returns a non-404 error, DataHubError is raised."""
    opensearch_bulk.return_value = (
        None,
        [
            {'delete': {'status': 404}},
            {'delete': {'status': 500}},
        ],
    )

    index = 'test-index'
    docs = [{'_id': 1}]

    with pytest.raises(DataHubError) as excinfo:
        delete_documents(index, docs)

    assert excinfo.value.args == (
        (
            "Errors during an OpenSearch bulk deletion operation: [{'delete': {'status': 500}}]"
        ),
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('synchronous_thread_pool')
def test_collector(monkeypatch, opensearch_with_signals):
    """
    Test that the collector collects and deletes all the django objects deleted.
    """
    obj = SimpleModel.objects.create()
    sync_object(SimpleModelSearchApp, str(obj.pk))
    opensearch_with_signals.indices.refresh()

    doc = SearchSimpleModel.to_document(obj, include_index=False, include_source=False)

    assert SimpleModel.objects.count() == 1

    collector = Collector()

    # check that the post/pre_delete callbacks of SimpleModel are in the collected
    # signal receivers to disable
    simplemodel_receivers = [
        receiver
        for receiver in collector.signal_receivers_to_disable
        if receiver.sender is SimpleModel
    ]
    assert simplemodel_receivers
    assert {receiver.signal for receiver in simplemodel_receivers} == {post_delete, pre_delete}

    # mock the receiver methods so that we can check they are called
    for receiver in collector.signal_receivers_to_disable:
        monkeypatch.setattr(receiver, 'enable', mock.Mock())
        monkeypatch.setattr(receiver, 'disable', mock.Mock())

    collector.connect()

    # check that the existing signal receivers are disabled
    for receiver in collector.signal_receivers_to_disable:
        assert receiver.disable.called
        assert not receiver.enable.called

    obj.delete()

    collector.disconnect()

    # check that the existing signal receivers are re-enabled
    for receiver in collector.signal_receivers_to_disable:
        assert receiver.enable.called

    assert collector.deletions == {
        SimpleModel: [doc],
    }

    read_alias = SearchSimpleModel.get_read_alias()

    assert SimpleModel.objects.count() == 0
    assert opensearch_with_signals.count(index=read_alias)['count'] == 1

    collector.delete_from_opensearch()

    opensearch_with_signals.indices.refresh()
    assert opensearch_with_signals.count(index=read_alias)['count'] == 0


@pytest.mark.django_db
@pytest.mark.usefixtures('synchronous_thread_pool')
def test_update_opensearch_after_deletions(
    opensearch_with_signals,
    queue: DataHubQueue,
):
    """
    Test that the context manager update_opensearch_after_deletions collects and deletes
    all the django objects deleted.
    """
    assert SimpleModel.objects.count() == 0

    obj = SimpleModel.objects.create()
    sync_object(SimpleModelSearchApp, str(obj.pk))
    opensearch_with_signals.indices.refresh()
    read_alias = SearchSimpleModel.get_read_alias()

    assert SimpleModel.objects.count() == 1
    assert opensearch_with_signals.count(index=read_alias)['count'] == 1

    with update_opensearch_after_deletions():
        obj.delete()

    opensearch_with_signals.indices.refresh()
    assert opensearch_with_signals.count(index=read_alias)['count'] == 0
