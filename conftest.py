import factory
import pytest
import requests_mock
from botocore.stub import Stubber
from django.conf import settings
from django.core.cache import CacheHandler
from django.core.management import call_command
from pytest_django.lazy_django import skip_if_no_django

from datahub.core.utils import get_s3_client


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Fixture for DB setup."""
    with django_db_blocker.unblock():
        call_command('loadinitialmetadata')


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
def requests_stubber():
    """Requests stubber based on requests-mock"""
    with requests_mock.mock() as requests_stubber:
        yield requests_stubber


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
