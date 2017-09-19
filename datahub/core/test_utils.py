import datetime
from secrets import token_hex

import pytest
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from oauth2_provider.models import AccessToken, Application
from rest_framework.test import APIClient

from datahub.oauth.scopes import Scope


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


class APITestMixin:
    """All the tests using the DB and accessing end points behind auth should use this class."""

    pytestmark = pytest.mark.django_db  # use db

    @property
    def user(self):
        """Return the user."""
        if not hasattr(self, '_user'):
            self._user = get_test_user()
        return self._user

    def get_token(self, *scopes):
        """Get access token for user test."""
        if not hasattr(self, '_tokens'):
            self._tokens = {}

        scope = ' '.join(scopes)

        if scope not in self._tokens:
            self._tokens[scope] = AccessToken.objects.create(
                user=self.user,
                application=self.application,
                token=token_hex(16),
                expires=datetime.datetime.now() + datetime.timedelta(hours=1),
                scope=scope
            )
        return self._tokens[scope]

    @property
    def api_client(self):
        """An API client with internal-front-end scope."""
        return self.create_api_client()

    def create_api_client(self, scope=Scope.internal_front_end, *additional_scopes):
        """Creates an API client associated with an OAuth token with the specified scope."""
        token = self.get_token(scope, *additional_scopes)
        client = APIClient()
        client.credentials(Authorization=f'Bearer {token}')
        return client

    @property
    def application(self):
        """Return the test application."""
        if not hasattr(self, '_application'):
            self._application, _ = Application.objects.get_or_create(
                user=self.user,
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_PASSWORD,
                name='Test client'
            )
        return self._application


def synchronous_executor_submit(fn, *args, **kwargs):
    """Run everything submitted to thread pools executor in sync."""
    fn(*args, **kwargs)


def synchronous_transaction_on_commit(fn):
    """During a test run a transaction is never committed, so we have to improvise."""
    fn()
