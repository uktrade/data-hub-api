from datetime import datetime, timedelta
from operator import attrgetter
from secrets import token_hex

import factory
import pytest
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.contrib.auth.models import Permission
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.test.client import Client
from django.urls import reverse
from django.utils.timezone import now
from oauth2_provider.models import AccessToken, Application
from rest_framework.fields import DateField, DateTimeField
from rest_framework.test import APIClient

from datahub.metadata.models import Team
from datahub.oauth.scopes import Scope


def get_default_test_user():
    """Return the test user."""
    user_model = get_user_model()
    try:
        test_user = user_model.objects.get(email='Testo@Useri.com')
    except user_model.DoesNotExist:
        team = Team.objects.filter(
            role__groups__name='DIT_staff'
        ).first()
        test_user = create_test_user(
            first_name='Testo',
            last_name='Useri',
            email='Testo@Useri.com',
            dit_team=team
        )
    return test_user


def create_test_user(permission_codenames=(), password=None, **user_attrs):
    """
    :returns: user
    :param permission_codenames: list of codename permissions to be
        applied to the user
    :param user_attrs: any user attribute
    """
    user_defaults = {
        'first_name': factory.Faker('first_name').generate({}),
        'last_name': factory.Faker('last_name').generate({}),
        'email': factory.Faker('email').generate({}),
        'date_joined': now()
    }
    user_defaults.update(user_attrs)

    user_model = get_user_model()
    user = user_model(**user_defaults)
    if password:
        user.set_password(password)
    user.save()

    permissions = Permission.objects.filter(codename__in=permission_codenames)
    user.user_permissions.set(permissions)

    return user


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
        assert client.login(username=user.email, password=self.PASSWORD)
        return client

    @staticmethod
    def login_url_with_redirect(redirect_url):
        """Returns the login URL with the redirect query param set."""
        return f'{reverse("admin:login")}?{REDIRECT_FIELD_NAME}={redirect_url}'


class APITestMixin:
    """All the tests using the DB and accessing end points behind auth should use this class."""

    pytestmark = pytest.mark.django_db  # use db

    @property
    def user(self):
        """Return the user."""
        if not hasattr(self, '_user'):
            self._user = get_default_test_user()
        return self._user

    def get_token(self, *scopes, grant_type=Application.GRANT_PASSWORD, user=None):
        """Get access token for user test."""
        if not hasattr(self, '_tokens'):
            self._tokens = {}

        if user is None and grant_type != Application.GRANT_CLIENT_CREDENTIALS:
            user = self.user

        scope = ' '.join(scopes)

        token_cache_key = (user.email if user else None, scope)
        if token_cache_key not in self._tokens:
            self._tokens[token_cache_key] = AccessToken.objects.create(
                user=user,
                application=self.get_application(grant_type),
                token=token_hex(16),
                expires=now() + timedelta(hours=1),
                scope=scope
            )
        return self._tokens[token_cache_key]

    @property
    def api_client(self):
        """An API client with data-hub:internal-front-end scope."""
        return self.create_api_client()

    def create_api_client(self, scope=Scope.internal_front_end, *additional_scopes,
                          grant_type=Application.GRANT_PASSWORD, user=None):
        """Creates an API client associated with an OAuth token with the specified scope."""
        token = self.get_token(scope, *additional_scopes, grant_type=grant_type, user=user)
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


def format_date_or_datetime(value):
    """
    Formats a date or datetime using DRF fields.

    This is for use in tests when comparing dates and datetimes with JSON-formatted values.
    """
    if isinstance(value, datetime):
        return DateTimeField().to_representation(value)
    return DateField().to_representation(value)


def random_obj_for_model(model):
    """Returns a random object for a model."""
    return random_obj_for_queryset(model.objects.all())


def random_obj_for_queryset(queryset):
    """Returns a random object for a queryset."""
    return queryset.order_by('?').first()


def get_attr_or_none(obj, attr):
    """
    Gets an attribute of an object, or None if the attribute does not exist.

    Dotted paths to attributes can be provided to specify nested attributes.

    Usage example:
        # Returns company.contact.name or None if contact is None
        get_attr_or_none(company, 'contact.name')
    """
    try:
        return attrgetter(attr)(obj)
    except AttributeError:
        return None


class MockQuerySet:
    """Mock version of QuerySet that represents a fixed set of items."""

    def __init__(self, items):
        """Initialises the mock query set."""
        self._items = items

    def __getitem__(self, item):
        """Returns an item."""
        return self._items[item]

    def __iter__(self):
        """Returns an iterator over the query set items."""
        return iter(self._items)

    def __len__(self):
        """Returns the number of items in the query set."""
        return len(self._items)

    def all(self):
        """Returns self."""
        return self

    def count(self):
        """Returns the number of items in the query set."""
        return len(self._items)

    def exists(self):
        """Returns whether there are any items in the query set."""
        return bool(self._items)

    def get(self, **kwargs):
        """Gets an item matching the given kwargs."""
        matches = [
            item for item in self._items
            if all(getattr(item, attr) == val for attr, val in kwargs.items())
        ]

        if not matches:
            raise ObjectDoesNotExist()

        if len(matches) > 1:
            raise MultipleObjectsReturned()

        return matches[0]

    def first(self):
        """Returns the first item."""
        return self._items[0] if self._items else None

    def iterator(self, chunk_size=None):
        """Returns an iterator over the query set items."""
        return iter(self._items)
