from unittest.mock import Mock

import factory
import pytest
from botocore.stub import Stubber
from django.conf import settings
from django.core.cache import CacheHandler
from django.core.management import call_command
from elasticsearch.helpers.test import get_test_client
from pytest_django.lazy_django import skip_if_no_django

from datahub.core.utils import get_s3_client
from datahub.metadata.test.factories import SectorFactory
from datahub.search import elasticsearch
from datahub.search.apps import get_search_apps


@pytest.fixture(scope='session')
def django_db_setup(pytestconfig, django_db_setup, django_db_blocker):
    """Fixture for DB setup."""
    reuse_db = pytestconfig.getoption('reuse_db')
    with django_db_blocker.unblock():
        call_command('loadinitialmetadata', force=reuse_db)


@pytest.fixture(scope='session', autouse=True)
def set_faker_locale():
    """Sets the default locale for Faker."""
    with factory.Faker.override_default_locale('en_GB'):
        yield


@pytest.fixture
def api_request_factory():
    """Django REST framework ApiRequestFactory instance."""
    skip_if_no_django()

    from rest_framework.test import APIRequestFactory

    return APIRequestFactory()


@pytest.fixture
def api_client():
    """Django REST framework ApiClient instance."""
    skip_if_no_django()

    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture()
def s3_stubber():
    """S3 stubber using the botocore Stubber class"""
    s3_client = get_s3_client()
    with Stubber(s3_client) as s3_stubber:
        yield s3_stubber


@pytest.fixture()
def local_memory_cache(monkeypatch):
    """Configure settings.CACHES to use LocMemCache."""
    monkeypatch.setitem(
        settings.CACHES,
        'default',
        {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
    )
    monkeypatch.setattr('django.core.cache.caches', CacheHandler())


@pytest.fixture
def synchronous_thread_pool(monkeypatch):
    """Run everything submitted to thread pools executor in sync."""
    monkeypatch.setattr(
        'datahub.core.thread_pool._submit_to_thread_pool',
        _synchronous_submit_to_thread_pool
    )


@pytest.fixture
def synchronous_on_commit(monkeypatch):
    """During a test run a transaction is never committed, so we have to improvise."""
    monkeypatch.setattr('django.db.transaction.on_commit', _synchronous_on_commit)


def _synchronous_submit_to_thread_pool(fn, *args, **kwargs):
    fn(*args, **kwargs)


def _synchronous_on_commit(fn):
    fn()


@pytest.fixture
def hierarchical_sectors():
    """Creates three test sectors in a hierarchy."""
    parent = None
    sectors = []

    for _ in range(3):
        sector = SectorFactory(parent=parent)
        sectors.append(sector)
        parent = sector

    yield sectors


# SEARCH

def pytest_generate_tests(metafunc):
    """Parametrises tests that use the `search_app` fixture."""
    if 'search_app' in metafunc.fixturenames:
        apps = get_search_apps()
        metafunc.parametrize(
            'search_app',
            apps,
            ids=[app.__class__.__name__ for app in apps]
        )


@pytest.fixture(scope='session')
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


@pytest.fixture(scope='session')
def _setup_es_indexes(_es_client):
    """Sets up ES and makes the client available."""
    _create_test_index(_es_client, settings.ES_INDEX)

    # Create models in the test index
    for search_app in get_search_apps():
        search_app.init_es()

    yield _es_client

    _es_client.indices.delete(settings.ES_INDEX)


@pytest.fixture
def setup_es(_setup_es_indexes, synchronous_on_commit, synchronous_thread_pool):
    """Sets up ES and deletes all the records after each run."""
    for search_app in get_search_apps():
        search_app.connect_signals()

    yield _setup_es_indexes

    for search_app in get_search_apps():
        search_app.disconnect_signals()

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


@pytest.fixture
def mock_es_client(monkeypatch):
    """Patches the Elasticsearch library so that a mock client is used."""
    mock_client = Mock()
    monkeypatch.setattr('elasticsearch_dsl.connections.connections.get_connection', mock_client)
    yield mock_client
