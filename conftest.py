import factory
import pytest
from botocore.stub import Stubber
from django.core.management import call_command
from pytest_django.lazy_django import skip_if_no_django

from datahub.core.utils import get_s3_client


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Fixture for DB setup."""
    with django_db_blocker.unblock():
        # force=True is not necessary, but saves a few seconds as it doesn't check if there is
        # any existing data
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


@pytest.fixture()
def s3_stubber():
    """S3 stubber using the botocore Stubber class"""
    s3_client = get_s3_client()
    with Stubber(s3_client) as s3_stubber:
        yield s3_stubber
