from unittest import mock

import pytest
from django.conf import settings
from django.db.models.signals import post_delete, pre_delete

from datahub.core.exceptions import DataHubException
from datahub.search.deletion import (
    BULK_CHUNK_SIZE,
    BULK_DELETION_TIMEOUT_SECS,
    Collector,
    delete_documents,
    update_es_after_deletions,
)
from datahub.search.sync_object import sync_object
from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.search.test.search_support.simplemodel.models import ESSimpleModel


@mock.patch('datahub.search.elasticsearch.es_bulk')
def test_delete_documents(es_bulk, mock_es_client):
    """Test that delete_documents calls ES bulk to delete all documents."""
    es_bulk.return_value = (None, [])

    index = 'test-index'
    es_docs = [
        {'_type': 'model', '_id': 1},
        {'_type': 'model', '_id': 2},
        {'_type': 'model', '_id': 3},
    ]
    delete_documents(index, es_docs)

    assert es_bulk.call_count == 1

    call_args, call_kwargs = es_bulk.call_args_list[0]
    call_kwargs['actions'] = list(call_kwargs['actions'])  # from generator to list
    assert call_args == (mock_es_client.return_value,)
    assert call_kwargs == {
        'actions': [
            {'_op_type': 'delete', '_index': index, **es_doc}
            for es_doc in es_docs
        ],
        'chunk_size': BULK_CHUNK_SIZE,
        'request_timeout': BULK_DELETION_TIMEOUT_SECS,
        'max_chunk_bytes': settings.ES_BULK_MAX_CHUNK_BYTES,
        'raise_on_error': False,
    }


@mock.patch('datahub.search.elasticsearch.es_bulk')
def test_delete_documents_with_errors(es_bulk, mock_es_client):
    """Test that if ES returns a non-404 error, DataHubException is raised."""
    es_bulk.return_value = (
        None,
        [
            {'delete': {'status': 404}},
            {'delete': {'status': 500}},
        ],
    )

    index = 'test-index'
    es_docs = [{'_type': 'model', '_id': 1}]

    with pytest.raises(DataHubException) as excinfo:
        delete_documents(index, es_docs)

    assert excinfo.value.args == (
        (
            'One or more errors during an Elasticsearch bulk deletion '
            "operation: [{'delete': {'status': 500}}]"
        ),
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('synchronous_thread_pool')
def test_collector(monkeypatch, es_with_signals):
    """
    Test that the collector collects and deletes all the django objects deleted.
    """
    obj = SimpleModel.objects.create()
    sync_object(SimpleModelSearchApp, str(obj.pk))
    es_with_signals.indices.refresh()

    es_doc = ESSimpleModel.es_document(obj, include_index=False, include_source=False)

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
        monkeypatch.setattr(receiver, 'connect', mock.Mock())
        monkeypatch.setattr(receiver, 'disconnect', mock.Mock())

    collector.connect()

    # check that the existing signal receivers are disconnected
    for receiver in collector.signal_receivers_to_disable:
        assert receiver.disconnect.called
        assert not receiver.connect.called

    obj.delete()

    collector.disconnect()

    # check that the existing signal receivers are connected back
    for receiver in collector.signal_receivers_to_disable:
        assert receiver.connect.called

    assert collector.deletions == {
        SimpleModel: [es_doc],
    }

    read_alias = ESSimpleModel.get_read_alias()

    assert SimpleModel.objects.count() == 0
    assert es_with_signals.count(read_alias, doc_type=SimpleModelSearchApp.name)['count'] == 1

    collector.delete_from_es()

    es_with_signals.indices.refresh()
    assert es_with_signals.count(read_alias, doc_type=SimpleModelSearchApp.name)['count'] == 0


@pytest.mark.django_db
@pytest.mark.usefixtures('synchronous_thread_pool')
def test_update_es_after_deletions(es_with_signals):
    """
    Test that the context manager update_es_after_deletions collects and deletes
    all the django objects deleted.
    """
    assert SimpleModel.objects.count() == 0

    obj = SimpleModel.objects.create()
    sync_object(SimpleModelSearchApp, str(obj.pk))
    es_with_signals.indices.refresh()
    read_alias = ESSimpleModel.get_read_alias()

    assert SimpleModel.objects.count() == 1
    assert es_with_signals.count(read_alias, doc_type=SimpleModelSearchApp.name)['count'] == 1

    with update_es_after_deletions():
        obj.delete()

    es_with_signals.indices.refresh()
    assert es_with_signals.count(read_alias, doc_type=SimpleModelSearchApp.name)['count'] == 0
