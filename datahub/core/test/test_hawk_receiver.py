import datetime
from collections.abc import Mapping

import mohawk
import pytest
from django.test import override_settings
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status


@pytest.fixture(autouse=True)
def test_urls():  # noqa: D403
    """pytest fixture to override the ROOT_URLCONF with test views."""
    with override_settings(ROOT_URLCONF='datahub.core.test.support.urls'):
        yield


def _url():
    return 'http://testserver' + reverse('test-hawk')


def _url_incorrect_domain():
    return 'http://incorrect' + reverse('test-hawk')


def _url_incorrect_path():
    return 'http://testserver' + reverse('test-hawk') + 'incorrect/'


def _auth_sender(
    key_id='test-id',
    secret_key='test-key',
    url=_url,
    method='GET',
    content='',
    content_type='',
):
    credentials = {
        'id': key_id,
        'key': secret_key,
        'algorithm': 'sha256',
    }
    return mohawk.Sender(
        credentials,
        url(),
        method,
        content=content,
        content_type=content_type,
    )


def _resolve_value(value):
    if isinstance(value, Mapping):
        return {item_key: _resolve_value(item_value) for item_key, item_value in value.items()}

    if callable(value):
        return value()

    return value


@pytest.mark.parametrize(
    'get_kwargs,expected_json',
    (
        (
            # If no X-Forwarded-For header
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender().request_header,
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If second-to-last X-Forwarded-For header isn't whitelisted
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender().request_header,
                'HTTP_X_FORWARDED_FOR': '9.9.9.9, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the only IP address in X-Forwarded-For is whitelisted
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender().request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the only IP address in X-Forwarded-For isn't whitelisted
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender().request_header,
                'HTTP_X_FORWARDED_FOR': '123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If third-to-last IP in X-Forwarded-For header is whitelisted
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender().request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 124.124.124, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If last of 3 IPs in X-Forwarded-For header is whitelisted
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender().request_header,
                'HTTP_X_FORWARDED_FOR': '124.124.124, 123.123.123.123, 1.2.3.4',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header isn't passed
            {
                'content_type': '',
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Authentication credentials were not provided.'},
        ),
        (
            # If the Authorization header generated from an incorrect ID
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender(key_id='incorrect').request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect secret
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender(secret_key='incorrect').request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect domain
            {
                'content_type': '',
                'HTTP_AUTHORIZATION':
                    lambda: _auth_sender(url=_url_incorrect_domain).request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect path
            {
                'content_type': '',
                'HTTP_AUTHORIZATION':
                    lambda: _auth_sender(url=_url_incorrect_path).request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect method
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender(method='POST').request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect
            # content-type
            {
                'content_type': '',
                'HTTP_AUTHORIZATION':
                    lambda: _auth_sender(content_type='incorrect').request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from incorrect content
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': lambda: _auth_sender(content='incorrect').request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
    ),
)
@pytest.mark.django_db
def test_401_returned(api_client, get_kwargs, expected_json):
    """If the request isn't properly Hawk-authenticated, then a 401 is
    returned
    """
    resolved_get_kwargs = _resolve_value(get_kwargs)
    response = api_client.get(
        _url(),
        **resolved_get_kwargs,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == expected_json


@pytest.mark.django_db
def test_if_61_seconds_in_past_401_returned(api_client):
    """If the Authorization header is generated 61 seconds in the past, then a
    401 is returned
    """
    past = datetime.datetime.now() - datetime.timedelta(seconds=61)
    with freeze_time(past):
        auth = _auth_sender().request_header
    response = api_client.get(
        reverse('test-hawk'),
        content_type='',
        HTTP_AUTHORIZATION=auth,
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = {'detail': 'Incorrect authentication credentials.'}
    assert response.json() == error


@pytest.mark.usefixtures('local_memory_cache')
@pytest.mark.django_db
def test_if_authentication_reused_401_returned(api_client):
    """If the Authorization header is reused, then a 401 is returned"""
    auth = _auth_sender().request_header

    response_1 = api_client.get(
        _url(),
        content_type='',
        HTTP_AUTHORIZATION=auth,
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )
    assert response_1.status_code == status.HTTP_200_OK

    response_2 = api_client.get(
        _url(),
        content_type='',
        HTTP_AUTHORIZATION=auth,
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )
    assert response_2.status_code == status.HTTP_401_UNAUTHORIZED
    error = {'detail': 'Incorrect authentication credentials.'}
    assert response_2.json() == error


@pytest.mark.django_db
def test_403_returned(api_client):
    """
    Test that a 403 is returned if the request is Hawk authenticated but the client doesn't have
    the required scope.
    """
    sender = _auth_sender(
        key_id='scopeless-id',
        secret_key='scopeless-key',
    )
    response = api_client.get(
        _url(),
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='3.3.3.3, 1.2.3.4, 123.123.123.123',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        'detail': 'You do not have permission to perform this action.',
    }


@pytest.mark.django_db
def test_empty_object_returned_with_authentication_3_ips(api_client):
    """If the Authorization and X-Forwarded-For headers are correct,
    with an extra IP address prepended to the X-Forwarded-For then
    the correct, and authentic, data is returned
    """
    sender = _auth_sender()
    response = api_client.get(
        _url(),
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='3.3.3.3, 1.2.3.4, 123.123.123.123',
    )

    assert response.status_code == status.HTTP_200_OK
    content = {'content': 'hawk-test-view'}
    assert response.json() == content


@pytest.mark.django_db
def test_empty_object_returned_with_authentication(api_client):
    """If the Authorization and X-Forwarded-For headers are correct, then
    the correct, and authentic, data is returned
    """
    sender = _auth_sender()
    response = api_client.get(
        _url(),
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )

    assert response.status_code == status.HTTP_200_OK
    content = {'content': 'hawk-test-view'}
    assert response.json() == content

    # Just asserting that accept_response doesn't raise is a bit weak,
    # so we also assert that it raises if the header, content, or
    # content_type are incorrect
    sender.accept_response(
        response_header=response['Server-Authorization'],
        content=response.content,
        content_type=response['Content-Type'],
    )
    with pytest.raises(mohawk.exc.MacMismatch):
        sender.accept_response(
            response_header='Hawk mac="incorrect", hash="incorrect"',
            content=response.content,
            content_type=response['Content-Type'],
        )
    with pytest.raises(mohawk.exc.MisComputedContentHash):
        sender.accept_response(
            response_header=response['Server-Authorization'],
            content='incorrect',
            content_type=response['Content-Type'],
        )
    with pytest.raises(mohawk.exc.MisComputedContentHash):
        sender.accept_response(
            response_header=response['Server-Authorization'],
            content=response.content,
            content_type='incorrect',
        )
