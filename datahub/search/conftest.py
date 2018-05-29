from unittest.mock import Mock

from django.conf import settings
from elasticsearch.helpers.test import get_test_client
from pytest import fixture

from datahub.metadata.test.factories import SectorFactory
from datahub.search import elasticsearch
from .apps import get_search_apps


def pytest_generate_tests(metafunc):
    """Parametrises tests that use the `search_app` fixture."""
    if 'search_app' in metafunc.fixturenames:
        apps = get_search_apps()
        metafunc.parametrize(
            'search_app',
            apps,
            ids=[app.__class__.__name__ for app in apps]
        )


@fixture(scope='session')
def _es_client(worker_id):
    """
    Makes the ES test helper client available.

    Also patches settings.ES_INDEX using the xdist worker ID so that each process gets a unique
    index when running tests using multiple processes using pytest -n.
    """
    # pytest's monkeypatch does not work in session fixtures, but there is no need to restore
    # the value so we just overwrite it normally
    settings.ES_INDEX = f'test_{worker_id}'

    from elasticsearch_dsl.connections import connections
    client = get_test_client(nowait=False)
    connections.add_connection('default', client)
    yield client


@fixture(scope='session')
def _setup_es_indexes(_es_client):
    """Sets up ES and makes the client available."""
    _create_test_index(_es_client, settings.ES_INDEX)

    # Create models in the test index
    for search_app in get_search_apps():
        search_app.init_es()
        search_app.connect_signals()

    yield _es_client

    _es_client.indices.delete(settings.ES_INDEX)

    for search_app in get_search_apps():
        search_app.disconnect_signals()


@fixture
def setup_es(_setup_es_indexes, synchronous_on_commit, synchronous_thread_pool):
    """Sets up ES and deletes all the records after each run."""
    yield _setup_es_indexes

    _setup_es_indexes.indices.refresh()
    _setup_es_indexes.delete_by_query(
        settings.ES_INDEX,
        body={'query': {'match_all': {}}}
    )
    _setup_es_indexes.indices.refresh()


def _create_test_index(client, index):
    """Creates/configures the test index."""
    if client.indices.exists(index=index):
        client.indices.delete(index)

    elasticsearch.configure_index(index, index_settings=settings.ES_INDEX_SETTINGS)


@fixture
def mock_es_client(monkeypatch):
    """Patches the Elasticsearch library so that a mock client is used."""
    mock_client = Mock()
    monkeypatch.setattr('elasticsearch_dsl.connections.connections.get_connection', mock_client)
    yield mock_client


@fixture
def hierarchical_sectors():
    """Creates three test sectors in a hierarchy."""
    parent = None
    sectors = []

    for _ in range(3):
        sector = SectorFactory(parent=parent)
        sectors.append(sector)
        parent = sector

    yield sectors
