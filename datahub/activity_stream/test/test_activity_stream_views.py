import mohawk
import pytest
from rest_framework import status
from rest_framework.reverse import reverse


def _url():
    return 'http://testserver' + reverse('api-v3:activity-stream:index')


def _auth_sender(
    key_id='some-id',
    secret_key='some-secret',
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


@pytest.mark.parametrize(
    'get_kwargs,expected_json',
    (
        (
            # If the Authorization header isn't passed
            {
                'content_type': '',
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Authentication credentials were not provided.'},
        ),
        (
            # If the wrong credentials are used
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': _auth_sender(
                    key_id='incorrect',
                    secret_key='incorrect',
                ).request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
    ),
)
@pytest.mark.django_db
def test_401_returned(api_client, get_kwargs, expected_json):
    """If the request isn't Hawk-authenticated, then a 401 is returned."""
    response = api_client.get(
        _url(),
        **get_kwargs,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == expected_json


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
def test_succeeds_with_valid_redentials(api_client):
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
    content = {'secret': 'content-for-pen-test'}
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
