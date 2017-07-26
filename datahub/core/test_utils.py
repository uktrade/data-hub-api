import datetime

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
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
        custom_perms = Permission.objects.filter(
            content_type__app_label__in=['company', 'investment', 'interaction']
        ).values_list('id', flat=True)
        test_user.user_permissions.set(custom_perms)
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

    @property
    def token(self):
        """Get access token for user test."""
        if not hasattr(self, '_token'):
            self._token = AccessToken(
                user=self.user,
                application=self.application,
                token='123456789',  # unsafe token, just for testing
                expires=datetime.datetime.now() + datetime.timedelta(hours=1),
                scope='write read'
            )
        return self._token.token

    @property
    def api_client(self):
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
