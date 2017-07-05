import datetime

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now
from oauth2_provider.models import AccessToken, Application
from rest_framework.test import APIClient


def get_test_user():
    """Return the test user."""
    user_model = get_user_model()
    try:
        test_user = user_model.objects.get(email='Testo@Useri.com')
    except user_model.DoesNotExist:
        test_user = user_model(
            first_name='Testo',
            last_name='Useri',
            email='Testo@Useri.com',
            date_joined=now(),
        )
        test_user.set_password('password')
        test_user.save()
    return test_user


class LeelooTestCase(TestCase):
    """All the tests using the DB and accessing end points behind auth should use this class."""

    pytestmark = pytest.mark.django_db  # use db

    def setUp(self):
        """Set ups some utils."""
        self._user = None
        self._application = None
        self._token = None
        self.user = self.get_user()
        self.application = self.get_application()
        self.token = self.get_token()
        self.api_client = self.get_logged_in_api_client()

    def get_user(self):
        """Return the user."""
        if self._user:
            return self._user
        return get_test_user()

    def get_logged_in_api_client(self):
        """
        Login using the OAuth2 authentication.

        1) Create an application instance, if necessary
        2) Generate the token
        3) Add the auth credentials to the header
        """
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.credentials(Authorization=f'Bearer {self.token}')
        return client

    def get_token(self):
        """Get access token for user test."""
        if self._token:
            return self._token

        token = AccessToken(
            user=self.user,
            application=self.application,
            token='123456789',  # unsafe token, just for testing
            expires=datetime.datetime.now() + datetime.timedelta(hours=1),
            scope='write read'
        )
        return token.token

    def get_application(self):
        """Return the test application."""
        if self._application:
            return self._application

        application, _ = Application.objects.get_or_create(
            user=get_test_user(),
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_PASSWORD,
            name='Test client'
        )
        return application


def synchronous_executor_submit(fn, *args, **kwargs):
    """Run everything submitted to thread pools executor in sync."""
    fn(*args, **kwargs)


def synchronous_transaction_on_commit(fn):
    """During a test run a transaction is never committed, so we have to improvise."""
    fn()
