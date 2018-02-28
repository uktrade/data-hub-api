from unittest import mock

from django.conf import settings
from elasticsearch.helpers.test import get_test_client
from pytest import fixture

from datahub.core.test_utils import synchronous_executor_submit, synchronous_transaction_on_commit
from datahub.search import elasticsearch
from .apps import get_search_apps


@fixture(scope='session')
def client(worker_id):
    """
    Makes the ES test helper client available.

    Also patches settings.ES_INDEX using the xdist worker ID so that each process gets a unique
    index when running tests using multiple processes using pytest -n.
    """
    with mock.patch.object(settings, 'ES_INDEX', new=f'test_{worker_id}'):
        from elasticsearch_dsl.connections import connections
        client = get_test_client(nowait=False)
        connections.add_connection('default', client)
        yield client


@fixture(scope='session')
def setup_es_indexes(client):
    """Sets up ES and makes the client available."""
    create_test_index(client, settings.ES_INDEX)

    # Create models in the test index
    for search_app in get_search_apps():
        search_app.init_es()
        search_app.connect_signals()

    with mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit), \
            mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit):

        yield client

    client.indices.delete(settings.ES_INDEX)

    for search_app in get_search_apps():
        search_app.disconnect_signals()


@fixture
def setup_es(setup_es_indexes):
    """Sets up ES and deletes all the records after each run."""
    yield setup_es_indexes

    setup_es_indexes.delete_by_query(
        settings.ES_INDEX,
        body={'query': {'match_all': {}}},
        ignore=(409,)
    )
    setup_es_indexes.indices.refresh()


def create_test_index(client, index):
    """Creates/configures the test index."""
    if client.indices.exists(index=index):
        client.indices.delete(index)

    elasticsearch.configure_index(index, settings.ES_INDEX_SETTINGS)
