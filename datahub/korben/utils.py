from hashlib import sha256
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.utils.timezone import now

from datahub.core import constants


def get_korben_user():
    """Get or return the Korben user."""
    user_model = get_user_model()
    try:
        korben_user = user_model.objects.get(email='kor.ben@foo.bar')
    except user_model.DoesNotExist:
        korben_user = user_model(
            email='kor.ben@foo.bar',
            first_name='Kor',
            last_name='Ben',
            date_joined=now(),
            dit_team_id=constants.Team.undefined.value.id,
        )
        korben_user.save()
    return korben_user


def string_to_bytes(obj):
    """Cast string to bytes."""
    if type(obj) is str:
        return bytes(obj, 'utf-8')
    return obj


def generate_signature(path, body, salt):
    """Generate the signature to be passed into the header."""
    # make sure it's a path
    url_object = urlparse(path)
    message = string_to_bytes(url_object.path) + string_to_bytes(body) + string_to_bytes(salt)
    return sha256(message).hexdigest()
