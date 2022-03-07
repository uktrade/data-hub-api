from unittest.mock import Mock

import factory
import pytest
from botocore.stub import Stubber
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.db.models.signals import post_save
from opensearchpy.helpers.test import get_test_client
from pytest_django.lazy_django import skip_if_no_django

from datahub.core.constants import AdministrativeArea
from datahub.core.test_utils import create_test_user, HawkAPITestClient
from datahub.dnb_api.utils import format_dnb_company
from datahub.documents.utils import get_s3_client_for_bucket
from datahub.metadata.test.factories import SectorFactory
from datahub.search.apps import get_search_app_by_model, get_search_apps
from datahub.search.bulk_sync import sync_objects
from datahub.search.opensearch import (
    alias_exists,
    create_index,
    delete_alias,
    delete_index,
    index_exists,
)
from datahub.search.signals import SignalReceiver


@pytest.fixture(scope='session')
def django_db_setup(pytestconfig, django_db_setup, django_db_blocker):
    """Fixture for DB setup."""
    with django_db_blocker.unblock():
        call_command('loadinitialmetadata', force=True)


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


@pytest.fixture
def hawk_api_client():
    """Hawk API client fixture."""
    yield HawkAPITestClient()


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
def local_memory_cache():
    """Get local memory cache."""
    yield

    cache.clear()


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
def _opensearch_client(worker_id):
    """
    Makes the OpenSearch test helper client available.

    Also patches settings.ES_INDEX_PREFIX using the xdist worker ID so that each process
    gets unique indices when running tests using multiple processes using pytest -n.
    """
    # pytest's monkeypatch does not work in session fixtures, but there is no need to restore
    # the value so we just overwrite it normally
    settings.OPENSEARCH_INDEX_PREFIX = f'test_{worker_id}'

    from opensearch_dsl.connections import connections
    client = get_test_client(nowait=False)
    connections.add_connection('default', client)
    yield client


@pytest.fixture(scope='session')
def _opensearch_session(_opensearch_client):
    """
    Session-scoped fixture that creates OpenSearch indexes that persist for the entire test
    session.
    """
    # Create models in the test index
    for search_app in get_search_apps():
        # Clean up in case of any aborted test runs
        index_name = search_app.search_model.get_target_index_name()
        read_alias = search_app.search_model.get_read_alias()
        write_alias = search_app.search_model.get_write_alias()

        if index_exists(index_name):
            delete_index(index_name)

        if alias_exists(read_alias):
            delete_alias(read_alias)

        if alias_exists(write_alias):
            delete_alias(write_alias)

        # Create indices and aliases
        alias_names = (read_alias, write_alias)
        create_index(
            index_name, search_app.search_model._doc_type.mapping, alias_names=alias_names,
        )

    yield _opensearch_client

    for search_app in get_search_apps():
        delete_index(search_app.search_model.get_target_index_name())


@pytest.fixture
def opensearch(_opensearch_session):
    """
    Function-scoped pytest fixture that:

    - ensures OpenSearch is available for the test
    - deletes all documents from OpenSearch at the end of the test.
    """
    yield _opensearch_session

    _opensearch_session.indices.refresh()
    indices = [search_app.search_model.get_target_index_name() for search_app in get_search_apps()]
    _opensearch_session.delete_by_query(
        indices,
        body={'query': {'match_all': {}}},
    )
    _opensearch_session.indices.refresh()


@pytest.fixture
def opensearch_with_signals(opensearch, synchronous_on_commit):
    """
    Function-scoped pytest fixture that:

    - ensures OpenSearch is available for the test
    - connects search signal receivers so that OpenSearch documents are automatically
    created for model instances saved during the test
    - deletes all documents from OpenSearch at the end of the test

    Use this fixture when specifically testing search signal receivers.

    Call opensearch_with_signals.indices.refresh() after creating objects to refresh all
    search indices and ensure synced objects are available for querying.
    """
    for search_app in get_search_apps():
        search_app.connect_signals()

    yield opensearch

    for search_app in get_search_apps():
        search_app.disconnect_signals()


class SavedObjectCollector:
    """
    Collects the search apps of saved search objects and indexes those apps in bulk in
    OpenSearch.
    """

    def __init__(self, opensearch_client, apps_to_collect):
        """
        Initialises the collector.

        :param apps_to_collect: the search apps to monitor the `post_save` signal for (and sync
            saved objects for when `flush_and_refresh()` is called)
        """
        self.collected_apps = set()
        self.opensearch_client = opensearch_client

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
        """Sync objects of all collected apps to OpenSearch and refresh search indices."""
        for search_app in self.collected_apps:
            search_model = search_app.search_model
            read_indices, write_index = search_model.get_read_and_write_indices()
            sync_objects(search_model, search_app.queryset.all(), read_indices, write_index)

        self.collected_apps.clear()
        self.opensearch_client.indices.refresh()

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
def opensearch_collector_context_manager(opensearch, synchronous_on_commit, request):
    """
    Slightly lower-level version of opensearch_with_collector.

    Function-scoped pytest fixture that:

    - ensures OpenSearch is available for the test
    - deletes all documents from OpenSearch at the end of the test
    - yields a context manager that can be used to collects all model objects saved so
    they can be synced to OpenSearch in bulk

    Call opensearch_collector_context_manager.flush_and_refresh() to sync collected objects to
    OpenSearch and refresh all indices.

    In most cases, you should not use this fixture directly, but use opensearch_with_collector or
    opensearch_with_signals instead.
    """
    marker_apps = {
        app
        for marker in request.node.iter_markers('opensearch_collector_apps')
        for app in marker.args
    }
    apps = marker_apps or get_search_apps()

    yield SavedObjectCollector(opensearch, apps)


@pytest.fixture
def opensearch_with_collector(opensearch_collector_context_manager):
    """
    Function-scoped pytest fixture that:

    - ensures OpenSearch is available for the test
    - collects all model objects saved so they can be synced to OpenSearch in bulk
    - deletes all documents from OpenSearch at the end of the test

    Use this fixture for search tests that don't specifically test signal receivers.

    Call opensearch_with_collector.flush_and_refresh() to sync collected objects to OpenSearch and
    refresh all indices.
    """
    with opensearch_collector_context_manager as collector:
        yield collector


@pytest.fixture
def mock_opensearch_client(monkeypatch):
    """Patches the OpenSearch library so that a mock client is used."""
    mock_client = Mock()
    monkeypatch.setattr('opensearch_dsl.connections.connections.get_connection', mock_client)
    yield mock_client


@pytest.fixture
def mock_connection_for_create_index(monkeypatch):
    """Patches the OpenSearch library so that a mock client is used."""
    mock_client = Mock()
    monkeypatch.setattr('opensearch_dsl.connections.connections.get_connection', mock_client)
    monkeypatch.setattr('opensearch_dsl.index.get_connection', mock_client)
    yield mock_client


@pytest.fixture
def dnb_response_uk():
    """
    Returns a UK-based DNB company.
    """
    return {
        'results': [
            {
                'address_country': 'GB',
                'address_county': '',
                'address_line_1': 'Unit 10, Ockham Drive',
                'address_line_2': '',
                'address_postcode': 'UB6 0F2',
                'address_town': 'GREENFORD',
                'annual_sales': 50651895.0,
                'annual_sales_currency': 'USD',
                'domain': 'foo.com',
                'duns_number': '123456789',
                'employee_number': 260,
                'global_ultimate_duns_number': '291332174',
                'global_ultimate_primary_name': 'FOO BICYCLE LIMITED',
                'industry_codes': [
                    {
                        'code': '336991',
                        'description': 'Motorcycle, Bicycle, and Parts Manufacturing',
                        'priority': 1,
                        'typeDescription': 'North American Industry Classification System 2017',
                        'typeDnbCode': 30832,
                    },
                    {
                        'code': '1927',
                        'description': 'Motorcycle Manufacturing',
                        'priority': 1,
                        'typeDescription': 'D&B Hoovers Industry Code',
                        'typeDnbCode': 25838,
                    },
                ],
                'is_annual_sales_estimated': None,
                'is_employees_number_estimated': True,
                'is_out_of_business': False,
                'legal_status': 'corporation',
                'primary_industry_codes': [
                    {
                        'usSicV4': '3751',
                        'usSicV4Description': 'Mfg motorcycles/bicycles',
                    },
                ],
                'primary_name': 'FOO BICYCLE LIMITED',
                'registered_address_country': 'GB',
                'registered_address_county': '',
                'registered_address_line_1': 'C/O LONE VARY',
                'registered_address_line_2': '',
                'registered_address_postcode': 'UB6 0F2',
                'registered_address_town': 'GREENFORD',
                'registration_numbers': [
                    {
                        'registration_number': '01261539',
                        'registration_type': 'uk_companies_house_number',
                    },
                ],
                'trading_names': [],
            },
        ],
    }


@pytest.fixture
def formatted_dnb_company(dnb_response_uk):
    """
    Get formatted DNB company data.
    """
    return format_dnb_company(dnb_response_uk['results'][0])


@pytest.fixture
def formatted_dnb_company_area(dnb_response_uk):
    """
    Get formatted DNB company data.
    """
    dnb_response_area = dnb_response_uk['results'][0].copy()
    dnb_response_area.update(
        address_area_abbrev_name=AdministrativeArea.texas.value.area_code,
    )
    return format_dnb_company(dnb_response_area)


@pytest.fixture
def search_support_user():
    """A user with permissions for search_support views."""
    return create_test_user(permission_codenames=['view_simplemodel', 'view_relatedmodel'])


def pytest_addoption(parser):
    """Adds a new flag to pytest to skip excluded tests"""
    parser.addoption(
        '--skip-excluded', '--se',
        action='store_true',
        default=False,
        help='Skip excluded tests from running',
    )


def pytest_collection_modifyitems(config, items):
    """Skip excluded tests"""
    if config.getoption('--skip-excluded') is False:
        return
    for item in items:
        if any([
            m.name == 'excluded' or m.name.startswith('excluded_')
            for m in item.iter_markers()
        ]):
            item.add_marker(pytest.mark.skip(reason='Test marked as excluded'))
