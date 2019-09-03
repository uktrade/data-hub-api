import mohawk


def sender(
    url,
    key_id='some-id',
    secret_key='some-secret',
    method='GET',
    content='',
    content_type='',
):
    """
    Return hawk sender for the given URL.
    """
    return mohawk.Sender(
        {
            'id': key_id,
            'key': secret_key,
            'algorithm': 'sha256',
        },
        url,
        method,
        content=content,
        content_type=content_type,
    )


def auth_header(
    url,
    key_id='some-id',
    secret_key='some-secret',
    method='GET',
    content='',
    content_type='',
):
    """
    Return HTTP_AUTHORIZATION header using hawk auth.
    """
    return sender(
        url,
        key_id=key_id,
        secret_key=secret_key,
        method=method,
        content=content,
        content_type=content_type,
    ).request_header


def get(client, url):
    """
    Returns the response of a HAWK authenticated get request.
    """
    return client.get(
        url,
        content_type='',
        HTTP_AUTHORIZATION=auth_header(url),
        HTTP_X_FORWARDED_FOR='3.3.3.3, 1.2.3.4, 123.123.123.123',
    )
