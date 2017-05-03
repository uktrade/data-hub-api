from pathlib import PurePath

import pytest
from datetime import datetime, timedelta

from django.core.management import call_command
from pytest_django.lazy_django import skip_if_no_django


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

def get_test_user():
    """Returns the test user."""
    from django.contrib.auth import get_user_model

    test_email = 'Testo@Useri.com'

    user_model = get_user_model()
    try:
        test_user = user_model.objects.get(email=test_email)
    except user_model.DoesNotExist:
        test_user = user_model(
            first_name='Testo',
            last_name='Useri',
            email=test_email,
            date_joined=datetime.now(),
        )
        test_user.set_password('password')
        test_user.save()
    return test_user

_application = None

def get_application():
    """Returns the test application."""
    if _application:
        return _application

    from oauth2_provider.models import Application

    application, _ = Application.objects.get_or_create(
        user=get_test_user(),
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
        name='Test client'
    )
    return application

@pytest.fixture
def logged_in_api_client():
    """Returns logged in client."""
    from rest_framework.test import APIClient
    from oauth2_provider.models import AccessToken

    user = get_test_user()

    token = AccessToken(
        user=user,
        application=get_application(),
        token='123456789',  # unsafe token, just for testing
        expires=datetime.now() + timedelta(hours=1),
        scope='write read'
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(Authorization='Bearer {token}'.format(token=token))
    return client
