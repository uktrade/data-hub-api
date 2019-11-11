from unittest.mock import Mock

import factory
import pytest
from botocore.stub import Stubber
from django.conf import settings
from django.core.cache import CacheHandler
from django.core.management import call_command
from django.db.models.signals import post_save
from elasticsearch.helpers.test import get_test_client
from pytest_django.lazy_django import skip_if_no_django

from datahub.documents.utils import get_s3_client_for_bucket
from datahub.metadata.test.factories import SectorFactory
from datahub.search.apps import get_search_app_by_model, get_search_apps
from datahub.search.bulk_sync import sync_objects
from datahub.search.elasticsearch import (
    alias_exists,
    create_index,
    delete_alias,
    delete_index,
    index_exists,
)
from datahub.search.signals import SignalReceiver


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
def es(_es_session):
    """
    Function-scoped pytest fixture that:

    - ensures Elasticsearch is available for the test
    - deletes all documents from Elasticsearch at the end of the test.
    """
    yield _es_session

    _es_session.indices.refresh()
    indices = [search_app.es_model.get_target_index_name() for search_app in get_search_apps()]
    _es_session.delete_by_query(
        indices,
        body={'query': {'match_all': {}}},
    )
    _es_session.indices.refresh()


@pytest.fixture
def es_with_signals(es, synchronous_on_commit):
    """
    Function-scoped pytest fixture that:

    - ensures Elasticsearch is available for the test
    - connects search signal receivers so that Elasticsearch documents are automatically
    created for model instances saved during the test
    - deletes all documents from Elasticsearch at the end of the test

    Use this fixture when specifically testing search signal receivers.

    Call es_with_signals.indices.refresh() after creating objects to refresh all search indices
    and ensure synced objects are available for querying.
    """
    for search_app in get_search_apps():
        search_app.connect_signals()

    yield es

    for search_app in get_search_apps():
        search_app.disconnect_signals()


class SavedObjectCollector:
    """
    Collects the search apps of saved search objects and indexes those apps in bulk in
    Elasticsearch.
    """

    def __init__(self, es_client, apps_to_collect):
        """
        Initialises the collector.

        :param apps_to_collect: the search apps to monitor the `post_save` signal for (and sync
            saved objects for when `flush_and_refresh()` is called)
        """
        self.collected_apps = set()
        self.es_client = es_client

        self.signal_receivers_to_connect = [
            SignalReceiver(post_save, search_app.queryset.model, self._collect)
            for search_app in set(apps_to_collect)
        ]

        # Disconnect all existing search post_save signal receivers (in case they were connected)
        self.signal_receivers_to_disable = [
            receiver
            for search_app in get_search_apps()
            for receiver in search_app.get_signal_receivers()
            if receiver.signal is post_save
        ]

    def __enter__(self):
        """Enable the collector by connecting our post_save signals."""
        for receiver in self.signal_receivers_to_connect:
            receiver.connect()

        for receiver in self.signal_receivers_to_disable:
            receiver.disable()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Disable the collector by disconnecting our post_save signals."""
        for receiver in self.signal_receivers_to_connect:
            receiver.disconnect()

        for receiver in self.signal_receivers_to_disable:
            receiver.enable()

    def flush_and_refresh(self):
        """Sync objects of all collected apps to Elasticsearch and refresh search indices."""
        for search_app in self.collected_apps:
            es_model = search_app.es_model
            read_indices, write_index = es_model.get_read_and_write_indices()
            sync_objects(es_model, search_app.queryset.all(), read_indices, write_index)

        self.collected_apps.clear()
        self.es_client.indices.refresh()

    def _collect(self, obj):
        """
        Logic run on post_save for models of all search apps.

        Note: This does not use transaction.on_commit(), because transactions in tests
        are not committed. Be careful if reusing this logic in production code (as you would
        usually want to delay syncing until the transaction is committed).
        """
        model = obj.__class__
        search_app = get_search_app_by_model(model)
        self.collected_apps.add(search_app)


@pytest.fixture
def es_with_collector(es, synchronous_on_commit, request):
    """
    Function-scoped pytest fixture that:

    - ensures Elasticsearch is available for the test
    - collects all model objects saved so they can be synced to Elasticsearch in bulk
    - deletes all documents from Elasticsearch at the end of the test

    Use this fixture for search tests that don't specifically test signal receivers.

    Call es_with_collector.flush_and_refresh() to sync collected objects to Elasticsearch and
    refresh all indices.
    """
    marker_apps = {
        app
        for marker in request.node.iter_markers('es_collector_apps')
        for app in marker.args
    }
    apps = marker_apps or get_search_apps()

    with SavedObjectCollector(es, apps) as collector:
        yield collector


@pytest.fixture
def mock_es_client(monkeypatch):
    """Patches the Elasticsearch library so that a mock client is used."""
    mock_client = Mock()
    monkeypatch.setattr('elasticsearch_dsl.connections.connections.get_connection', mock_client)
    yield mock_client
