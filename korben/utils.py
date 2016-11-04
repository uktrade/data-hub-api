from hashlib import sha256
from urllib.parse import urlparse

from django.contrib.auth import get_user_model


def get_korben_user():
    """Get or return the Korben user."""

    user_model = get_user_model()
    korben, _ = user_model.objects.get_or_create(username='Korben', first_name='Kor', last_name='Ben')
    return korben


def string_to_bytes(obj):
    if type(obj) is str:
        return bytes(obj, 'utf-8')
    return obj


def generate_signature(path, body, salt):
    """Generate the signature to be passed into the header."""

    # make sure it's a path
    url_object = urlparse(path)

    message = string_to_bytes(url_object.path) + string_to_bytes(body) + string_to_bytes(salt)
    return sha256(message).hexdigest()
