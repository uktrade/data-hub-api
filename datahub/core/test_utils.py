from datetime import datetime, timedelta
from secrets import token_hex

import pytest
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.utils.timezone import now
from oauth2_provider.models import AccessToken, Application
from rest_framework.fields import DateField, DateTimeField
from rest_framework.test import APIClient

from datahub.metadata.models import Team
from datahub.oauth.scopes import Scope


def get_test_user(team=None):
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
        if team is None:
            test_user.dit_team = Team.objects.filter(
                role__team_role_groups__name='DIT_staff'
            ).first()
        else:
            test_user.dit_team = team

        test_user.set_password('password')
        test_user.save()
    return test_user


def get_admin_user(password=None):
    """Return the test admin user."""
    email = 'powerfuluser@trade.dit'
    user_model = get_user_model()
    try:
        admin_user = user_model.objects.get(email=email)
    except user_model.DoesNotExist:
        admin_user = user_model.objects.create_superuser(email=email, password=password)
    return admin_user


class AdminTestMixin:
    """All the tests using the DB and accessing admin endpoints should use this class."""

    pytestmark = pytest.mark.django_db  # use db

    PASSWORD = 'password'

    @property
    def user(self):
        """Returns admin user."""
        if not hasattr(self, '_user'):
            self._user = get_admin_user(self.PASSWORD)
        return self._user

    @property
    def client(self):
        """Returns an authenticated admin client."""
        return self.create_client()

    def create_client(self, user=None):
        """Creates a client with admin access."""
        if not user:
            user = self.user
        client = Client()
        client.login(username=user.email, password=self.PASSWORD)
        return client


class APITestMixin:
    """All the tests using the DB and accessing end points behind auth should use this class."""

    pytestmark = pytest.mark.django_db  # use db

    @property
    def user(self):
        """Return the user."""
        if not hasattr(self, '_user'):
            self._user = get_test_user()
        return self._user

    def get_token(self, *scopes, grant_type=Application.GRANT_PASSWORD):
        """Get access token for user test."""
        if not hasattr(self, '_tokens'):
            self._tokens = {}

        scope = ' '.join(scopes)

        if scope not in self._tokens:
            self._tokens[scope] = AccessToken.objects.create(
                user=self.user,
                application=self.get_application(grant_type),
                token=token_hex(16),
                expires=now() + timedelta(hours=1),
                scope=scope
            )
        return self._tokens[scope]

    @property
    def api_client(self):
        """An API client with data-hub:internal-front-end scope."""
        return self.create_api_client()

    def create_api_client(self, scope=Scope.internal_front_end, *additional_scopes,
                          grant_type=Application.GRANT_PASSWORD):
        """Creates an API client associated with an OAuth token with the specified scope."""
        token = self.get_token(scope, *additional_scopes, grant_type=grant_type)
        client = APIClient()
        client.credentials(Authorization=f'Bearer {token}')
        return client

    def get_application(self, grant_type=Application.GRANT_PASSWORD):
        """Return a test application with the specified grant type."""
        if not hasattr(self, '_applications'):
            self._applications = {}

        if grant_type not in self._applications:
            self._applications[grant_type] = Application.objects.create(
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=grant_type,
                name=f'Test client ({grant_type})'
            )
        return self._applications[grant_type]


def synchronous_executor_submit(fn, *args, **kwargs):
    """Run everything submitted to thread pools executor in sync."""
    fn(*args, **kwargs)


def synchronous_transaction_on_commit(fn):
    """During a test run a transaction is never committed, so we have to improvise."""
    fn()


def format_date_or_datetime(value):
    """
    Formats a date or datetime using DRF fields.

    This is for use in tests when comparing dates and datetimes with JSON-formatted values.
    """
    if isinstance(value, datetime):
        return DateTimeField().to_representation(value)
    return DateField().to_representation(value)
