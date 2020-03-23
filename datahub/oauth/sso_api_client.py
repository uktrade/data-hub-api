from django.conf import settings
from requests import RequestException
from rest_framework import serializers, status

from datahub.core.api_client import APIClient, TokenAuth


class SSORequestError(Exception):
    """An SSO API request error."""

    def __init__(self, message, response=None):
        """Initialise the exception."""
        self.message = message
        self.response = response


class SSOTokenDoesNotExist(Exception):
    """The token does not exist."""


class SSOUserDoesNotExist(Exception):
    """The token does not exist."""


class IntrospectionSerializer(serializers.Serializer):
    """
    Serializer used only to validate introspection responses.

    Note: This includes only the fields we care about.
    """

    active = serializers.BooleanField()
    username = serializers.CharField()
    email_user_id = serializers.EmailField()
    exp = serializers.IntegerField()


def introspect_token(token):
    """Get details about an access token from the introspection endpoint in Staff SSO."""
    try:
        return _request(
            'post',
            'o/introspect/',
            response_serializer_class=IntrospectionSerializer,
            data={'token': token},
        )
    except SSORequestError as exc:
        # SSO returns a 401 if the token is invalid (non-existent)
        # So this is treated as a special case
        if exc.response is not None and exc.response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise SSOTokenDoesNotExist()
        raise


def get_user_by_email(email):
    """
    Look up details about a user in Staff SSO using an email address.

    Any of a user's email addresses can be specified.
    """
    return _get_user(email=email)


def get_user_by_email_user_id(email_user_id):
    """Look up details about a user in Staff SSO using their unique email user ID."""
    return _get_user(email_user_id=email_user_id)


def _get_user(**params):
    try:
        return _request('get', 'api/v1/user/introspect/', params=params)
    except SSORequestError as exc:
        if exc.response is not None and exc.response.status_code == status.HTTP_404_NOT_FOUND:
            raise SSOUserDoesNotExist()
        raise


def _request(method, path, response_serializer_class=None, **kwargs):
    """
    Internal utility function to make a generic API request to Staff SSO.

    As this deals with authentication, this aims to be more robust than might be the case
    for other API requests.
    """
    api_client = _get_api_client()

    try:
        response = api_client.request(method, path, **kwargs)
    except RequestException as exc:
        raise SSORequestError('SSO request failed', response=exc.response) from exc

    try:
        response_data = response.json()
    except ValueError as exc:
        raise SSORequestError('SSO response parsing failed') from exc

    if not response_serializer_class:
        return response_data

    try:
        serializer = response_serializer_class(data=response_data)
        serializer.is_valid(raise_exception=True)
    except serializers.ValidationError as exc:
        raise SSORequestError('SSO response validation failed') from exc

    return serializer.validated_data


def _get_api_client():
    return APIClient(
        settings.STAFF_SSO_BASE_URL,
        TokenAuth(settings.STAFF_SSO_AUTH_TOKEN, token_keyword='Bearer'),
        default_timeout=settings.STAFF_SSO_REQUEST_TIMEOUT,
    )
