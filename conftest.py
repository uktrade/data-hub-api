from unittest.mock import Mock

import factory
import pytest
from botocore.stub import Stubber
from django.conf import settings
from django.core.cache import CacheHandler
from django.core.management import call_command
from elasticsearch.helpers.test import get_test_client
from pytest_django.lazy_django import skip_if_no_django

from datahub.documents.utils import get_s3_client_for_bucket
from datahub.metadata.test.factories import SectorFactory
from datahub.search.apps import get_search_apps
from datahub.search.elasticsearch import (
    alias_exists,
    create_index,
    delete_alias,
    delete_index,
    index_exists,
)


def pytest_sessionstart(session):
    """
    Set tests to use all databases.

    pytest-django does not directly support the databases attribute, so this is a workaround.

    See PRs #397, #416 and #437 in the pytest-django repository on GitHub for more information.
    """
    from django.test import TestCase, TransactionTestCase

    databases_to_enable = {'default', 'mi'}
    TransactionTestCase.databases = databases_to_enable
    TestCase.databases = databases_to_enable


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


class _ReturnValueTracker:
    def __init__(self, cls, method_name):
        self.return_values = []
        self.original_callable = getattr(cls, method_name)

    def make_mock(self):
        def _spy(*args, **kwargs):
            return_value = self.original_callable(*args, **kwargs)
            self.return_values.append(return_value)
            return return_value

        return _spy


@pytest.fixture
def track_return_values(monkeypatch):
    """
    Fixture that can be used to track the return values of a callable.

    Usage example:

        # obj could be a class or a module (for example)
        def test_something(track_return_values):
            tracker = track_return_values(obj, 'name_of_callable')

            ...

            assert tracker.return_values == [1, 2, 3]
    """
    def _patch(obj, callable_name):
        tracker = _ReturnValueTracker(obj, callable_name)
        monkeypatch.setattr(obj, callable_name, tracker.make_mock())
        return tracker

    yield _patch


@pytest.fixture()
def s3_stubber():
    """S3 stubber using the botocore Stubber class."""
    s3_client = get_s3_client_for_bucket('default')
    with Stubber(s3_client) as s3_stubber:
        yield s3_stubber


@pytest.fixture()
def local_memory_cache(monkeypatch):
    """Configure settings.CACHES to use LocMemCache."""
    monkeypatch.setitem(
        settings.CACHES,
        'default',
        {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    )
    cache_handler = CacheHandler()
    monkeypatch.setattr('django.core.cache.caches', cache_handler)

    yield

    cache_handler['default'].clear()


@pytest.fixture
def synchronous_thread_pool(monkeypatch):
    """Run everything submitted to thread pools executor in sync."""
    monkeypatch.setattr(
        'datahub.core.thread_pool._submit_to_thread_pool',
        _synchronous_submit_to_thread_pool,
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

@pytest.fixture(scope='session')
def _es_client(worker_id):
    """
    Makes the ES test helper client available.

    Also patches settings.ES_INDEX_PREFIX using the xdist worker ID so that each process
    gets unique indices when running tests using multiple processes using pytest -n.
    """
    # pytest's monkeypatch does not work in session fixtures, but there is no need to restore
    # the value so we just overwrite it normally
    settings.ES_INDEX_PREFIX = f'test_{worker_id}'

    from elasticsearch_dsl.connections import connections
    client = get_test_client(nowait=False)
    connections.add_connection('default', client)
    yield client


@pytest.fixture(scope='session')
def _es_session(_es_client):
    """
    Session-scoped fixture that creates Elasticsearch indexes that persist for the entire test
    session.
    """
    # Create models in the test index
    for search_app in get_search_apps():
        # Clean up in case of any aborted test runs
        index_name = search_app.es_model.get_target_index_name()
        read_alias = search_app.es_model.get_read_alias()
        write_alias = search_app.es_model.get_write_alias()

        if index_exists(index_name):
            delete_index(index_name)

        if alias_exists(read_alias):
            delete_alias(read_alias)

        if alias_exists(write_alias):
            delete_alias(write_alias)

        # Create indices and aliases
        alias_names = (read_alias, write_alias)
        create_index(index_name, search_app.es_model._doc_type.mapping, alias_names=alias_names)

    yield _es_client

    for search_app in get_search_apps():
        delete_index(search_app.es_model.get_target_index_name())


@pytest.fixture
def es_with_signals(_es_session, synchronous_on_commit):
    """
    Function-scoped pytest fixture that:

    - ensures Elasticsearch is available for the test
    - connects search signal receivers so that Elasticsearch documents are automatically
    created for model instances saved during the test
    - deletes all documents from Elasticsearch at the end of the test
    """
    for search_app in get_search_apps():
        search_app.connect_signals()

    yield _es_session

    for search_app in get_search_apps():
        search_app.disconnect_signals()

    _es_session.indices.refresh()
    indices = [search_app.es_model.get_target_index_name() for search_app in get_search_apps()]
    _es_session.delete_by_query(
        indices,
        body={'query': {'match_all': {}}},
    )
    _es_session.indices.refresh()


@pytest.fixture
def mock_es_client(monkeypatch):
    """Patches the Elasticsearch library so that a mock client is used."""
    mock_client = Mock()
    monkeypatch.setattr('elasticsearch_dsl.connections.connections.get_connection', mock_client)
    yield mock_client
