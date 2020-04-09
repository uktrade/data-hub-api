import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from operator import attrgetter
from secrets import token_hex
from unittest import mock

import factory
import mohawk
import pytest
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.contrib.auth.models import Permission
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.test.client import Client
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timezone import now
from oauth2_provider.models import AccessToken, Application
from rest_framework.fields import DateField, DateTimeField
from rest_framework.test import APIClient

from datahub.core.utils import join_truthy_strings
from datahub.metadata.models import Team
from datahub.oauth.scopes import Scope


class HawkAPITestClient:
    """Simple test client for making requests signed using Hawk."""

    DEFAULT_HTTP_X_FORWARDED_FOR = '1.2.3.4, 123.123.123.123'
    unset = object()

    def __init__(self):
        """Initialise the client and create an APIClient instance."""
        self.api_client = APIClient()
        self.credentials = None
        self.http_x_forwarded_for = self.DEFAULT_HTTP_X_FORWARDED_FOR

    def set_credentials(self, id_, key, algorithm='sha256'):
        """Set the credentials for requests."""
        self.credentials = {
            'id': id_,
            'key': key,
            'algorithm': algorithm,
        }

    def set_http_x_forwarded_for(self, http_x_forwarded_for):
        """Set client IP addresses."""
        self.http_x_forwarded_for = http_x_forwarded_for

    def get(self, path, params=None):
        """Make a GET request (optionally with query params)."""
        return self.request('get', path, params=params)

    def post(self, path, json_):
        """Make a POST request with a JSON body."""
        return self.request('post', path, json_=json_)

    def put(self, path, json_):
        """Make a PUT request with a JSON body."""
        return self.request('put', path, json_=json_)

    def patch(self, path, json_):
        """Make a PATCH request with a JSON body."""
        return self.request('patch', path, json_=json_)

    def delete(self, path, json_):
        """Make a DELETE request with a JSON body."""
        return self.request('delete', path, json_=json_)

    def request(self, method, path, params=None, json_=unset, content_type=''):
        """Make a request with a specified HTTP method."""
        params = urlencode(params) if params else ''
        url = join_truthy_strings(f'http://testserver{path}', params, sep='?')

        if json_ is not self.unset:
            content_type = 'application/json'
            body = json.dumps(json_, cls=DjangoJSONEncoder).encode('utf-8')
        else:
            body = b''

        sender = mohawk.Sender(
            self.credentials,
            url,
            method,
            content=body,
            content_type=content_type,
        )

        return self.api_client.generic(
            method,
            url,
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_X_FORWARDED_FOR=self.http_x_forwarded_for,
            data=body,
            content_type=content_type,
        )


def get_default_test_user():
    """Return the test user."""
    user_model = get_user_model()
    try:
        test_user = user_model.objects.get(email='Testo@Useri.com')
    except user_model.DoesNotExist:
        team = Team.objects.filter(
            role__groups__name='DIT_staff',
        ).first()
        test_user = create_test_user(
            first_name='Testo',
            last_name='Useri',
            email='Testo@Useri.com',
            dit_team=team,
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
        'date_joined': now(),
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
        if not hasattr(self, '_client'):
            self._client = self.create_client()
        return self._client

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
                scope=scope,
            )
        return self._tokens[token_cache_key]

    @property
    def api_client(self):
        """An API client with data-hub:internal-front-end scope."""
        if not hasattr(self, '_client'):
            self._api_client = self.create_api_client()
        return self._api_client

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
                name=f'Test client ({grant_type})',
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

    def __init__(self, objects, value_list_fields=None, value_list_flat=None):
        """Initialises the mock query set."""
        self._objects = objects
        self._value_list_fields = value_list_fields
        self._value_list_flat = value_list_flat

    def __getitem__(self, item):
        """Returns an item."""
        return self._results[item]

    def __iter__(self):
        """Returns an iterator over the query set items."""
        return iter(self._results)

    def __len__(self):
        """Returns the number of items in the query set."""
        return len(self._results)

    def all(self):
        """Returns self."""
        return self

    def count(self):
        """Returns the number of items in the query set."""
        return len(self._results)

    def exists(self):
        """Returns whether there are any items in the query set."""
        return bool(self._results)

    def get(self, **kwargs):
        """Gets an item matching the given kwargs."""
        matches = [
            item for item in self._results
            if all(getattr(item, attr) == val for attr, val in kwargs.items())
        ]

        if not matches:
            raise ObjectDoesNotExist()

        if len(matches) > 1:
            raise MultipleObjectsReturned()

        return matches[0]

    def filter(self, pk__in=()):
        """
        Filters the query set.

        Only supports filtering using pk__in at present.
        """
        field = self._map_field('pk')
        filtered_objects = [obj for obj in self._objects if getattr(obj, field) in pk__in]
        return self._clone(filtered_objects)

    def first(self):
        """Returns the first item."""
        return self._results[0] if self._results else None

    def iterator(self, chunk_size=None):
        """Returns an iterator over the query set items."""
        return iter(self._results)

    def values_list(self, *fields, flat=False):
        """Creates a clone of the query set with results returned as tuples."""
        if flat:
            assert len(fields) == 1

        return self._clone(value_list_fields=fields, value_list_flat=flat)

    def _clone(self, objects=None, **kwargs):
        clone_args = (
            objects if objects is not None else self._objects,
        )
        clone_kwargs = {
            'value_list_fields': self._value_list_fields,
            'value_list_flat': self._value_list_flat,
            **kwargs,
        }

        return MockQuerySet(*clone_args, **clone_kwargs)

    @property
    def _results(self):
        if self._value_list_fields is None:
            return self._objects

        if self._value_list_flat:
            field = self._map_field(self._value_list_fields[0])

            return [getattr(obj, field) for obj in self._objects]

        return [
            tuple(getattr(obj, field) for field in self._value_list_fields)
            for obj in self._objects
        ]

    @staticmethod
    def _map_field(field):
        return 'id' if field == 'pk' else field


def join_attr_values(iterable, attr='name', separator=', '):
    """
    Takes all values of a specified attribute for the items of an iterable, sorts the values and
    joins them using a separator.

    attr can also be a dotted path (to specify sub-attributes).
    """
    getter = attrgetter(attr)
    return separator.join(getter(value) for value in iterable)


def format_csv_data(rows):
    """
    Converts source data into formatted strings as should be written to CSV exports.

    Expects an iterable of dictionaries with arbitrary objects as values, and outputs a list of
    dictionaries with strings as values.
    """
    return [
        {key: _format_csv_value(val) for key, val in row.items()} for row in rows
    ]


def _format_csv_value(value):
    """Converts a value to a string in the way that is expected in CSV exports."""
    if value is None:
        return ''
    if isinstance(value, Decimal):
        normalized_value = value.normalize()
        return f'{normalized_value:f}'
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)


def construct_mock(**props):
    """
    Same as mock.Mock() but using configure_mock as
    name collides with the kwarg in the Mock constructor.
    """
    obj = mock.Mock(spec_set=tuple(props))
    obj.configure_mock(**props)
    return obj


def str_or_none(value):
    """Returns string casted value if given value is not None"""
    return str(value) if value is not None else value


def identity(value):
    """Pass through a single argument unchanged."""
    return value


def resolve_data(data, value_resolver=identity):
    """
    Recursively resolve callables in data structures.

    Given a value:

    - if it's a callable, resolve it
    - if it's a sequence, resolve each of the sequence's values
    - if it's a dict, resolve each value of the dict

    The resolved value is returned.

    Used in parametrised tests.
    """
    if isinstance(data, Mapping):
        return {
            key: resolve_data(value, value_resolver=value_resolver)
            for key, value in data.items()
        }

    if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        return [resolve_data(value, value_resolver=value_resolver) for value in data]

    if callable(data):
        return value_resolver(data())

    return value_resolver(data)


def resolve_objects(data, object_resolver=attrgetter('pk')):  # noqa: B008
    """
    Recursively resolve callables in data structures and also resolve model objects to pk values.

    Used in parametrised tests.
    """

    def resolve_value(value):
        if hasattr(value, 'pk'):
            return object_resolver(value)
        return value

    return resolve_data(data, value_resolver=resolve_value)


class HawkMockJSONResponse:
    """
    Mock utility mocking server validation for POST content.
    This is needed when mocking responses when using the APIClient and HawkAuth.

    The default reponse is an empty JSON but can be overridden by passing in a
    response argument into the constructor.

    dynamic_reponse = HawkMockJSONResponse(
        api_id='some-id',
        api_key='some-key'
        response={'content': 'Hello'}
    )

    requests_mock.post(
        'some/api/',
        status_code=status.HTTP_200_OK,
        json=dynamic_reponse,
    )
    """

    def __init__(
        self,
        api_id,
        api_key,
        algorithm='sha256',
        content_type='application/json',
        response=None,
    ):
        """
        Initialise with a dict that can be serialized to json
        this reponse body will be validated and returned in the mock reponse.
        """
        self.credentials = {
            'id': api_id,
            'key': api_key,
            'algorithm': algorithm,
        }
        self._response = response
        self.content_type = content_type
        if self._response is None:
            self._response = {}

    def __call__(self, request, context):
        """
        Mock the server authorization response for validating the response content
        """
        response = json.dumps(self._response)
        credentials = (lambda key: self.credentials)
        receiver = mohawk.Receiver(
            credentials,
            request.headers['Authorization'],
            request.url,
            request.method,
            content=request.text,
            content_type=request.headers.get('Content-Type', ''),
        )
        receiver.respond(
            content=response,
            content_type=self.content_type,
        )
        context.headers['Server-Authorization'] = receiver.response_header
        context.headers['Content-Type'] = self.content_type
        return response
