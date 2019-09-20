import mohawk
import pytest
from rest_framework import status

from datahub.activity_stream.test import hawk
from datahub.activity_stream.test.utils import get_url


ACTIVITY_STREAM_URLS = (
    'api-v3:activity-stream:interactions',
    'api-v3:activity-stream:investment-project-added',
    'api-v3:activity-stream:omis-order-added',
)


@pytest.mark.parametrize(
    'endpoint',
    ACTIVITY_STREAM_URLS,
)
@pytest.mark.django_db
def test_401_noauth(api_client, endpoint):
    """If the request isn't Hawk-authenticated, then a 401 is returned."""
    response = api_client.get(
        get_url(endpoint),
        content_type='',
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',

    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        'detail': 'Authentication credentials were not provided.',
    }


@pytest.mark.parametrize(
    'endpoint',
    ACTIVITY_STREAM_URLS,
)
@pytest.mark.django_db
def test_401_wrong_creds(api_client, endpoint):
    """If the request has invalid Hawk credentials, then a 401 is returned."""
    response = api_client.get(
        get_url(endpoint),
        content_type='',
        HTTP_AUTHORIZATION=hawk.auth_header(
            get_url('api-v3:activity-stream:interactions'),
            key_id='incorrect',
            secret_key='incorrect',
        ),
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        'detail': 'Incorrect authentication credentials.',
    }


@pytest.mark.parametrize(
    'endpoint',
    ACTIVITY_STREAM_URLS,
)
@pytest.mark.django_db
def test_401_wrong_ip_adress(api_client, endpoint):
    """If the request has an invalid client IP address, then a 403 is returned."""
    url = get_url(endpoint)
    sender = hawk.sender(url)
    response = api_client.get(
        url,
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='9.10.11.12, 5.6.7.8',
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        'detail': 'Incorrect authentication credentials.',
    }


@pytest.mark.parametrize(
    'endpoint',
    ACTIVITY_STREAM_URLS,
)
@pytest.mark.django_db
def test_403_returned(api_client, endpoint):
    """
    Test that a 403 is returned if the request is Hawk authenticated but the client doesn't have
    the required scope.
    """
    url = get_url(endpoint)
    sender = hawk.sender(
        url,
        key_id='test-id-without-scope',
        secret_key='test-key-without-scope',
    )
    response = api_client.get(
        url,
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='3.3.3.3, 1.2.3.4, 123.123.123.123',
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        'detail': 'You do not have permission to perform this action.',
    }


@pytest.mark.parametrize(
    'endpoint',
    ACTIVITY_STREAM_URLS,
)
@pytest.mark.django_db
def test_succeeds_with_valid_credentials(api_client, endpoint):
    """If the Authorization and X-Forwarded-For headers are correct, then
    the correct, and authentic, data is returned
    """
    url = get_url(endpoint)
    sender = hawk.sender(url)
    response = api_client.get(
        url,
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )
    assert response.status_code == status.HTTP_200_OK

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
