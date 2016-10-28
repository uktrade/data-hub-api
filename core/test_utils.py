import datetime

import pytest
from django.contrib.auth.models import User
from oauth2_provider.models import Application, AccessToken
from rest_framework.test import APIClient


def get_test_user():
    """Return the test user."""

    test, _ = User.objects.get_or_create(username='Test')
    test.set_password('password')
    return test


class LeelooTestCase:
    """All the tests using the DB and accessing end points behind auth should use this class."""

    pytestmark = pytest.mark.django_db  # use db

    def __init__(self):
        self._user = None
        self._application = None
        self._token = None
        self.user = self.get_user()
        self.application = self.get_application()
        self.token = self.get_token()

    def get_user(self):
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
        client.credentials(Authorization='Bearer {token}'.format(token=self.token))
        return client

    def get_token(self):
        """Get access token for user test."""

        if self._token:
            return self._token

        token = AccessToken(
            user=self.user,
            application=self.application,
            token='123456789',
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
