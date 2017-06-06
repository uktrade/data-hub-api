from pathlib import PurePath

import pytest
from django.core.management import call_command
from pytest_django.lazy_django import skip_if_no_django

from datahub.search import elasticsearch


def pytest_configure():
    elasticsearch.ES_INDEX = 'test'


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    fixtures_dir = PurePath(__file__).parent / 'fixtures'
    with django_db_blocker.unblock():
        call_command('loaddata', fixtures_dir / 'metadata.yaml')
        call_command('loaddata', fixtures_dir / 'datahub_businesstypes.yaml')


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
