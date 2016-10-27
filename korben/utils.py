from hashlib import sha256

from django.contrib.auth.models import User


def get_korben_user():
    """Get or return the Korben user."""

    korben, _ = User.objects.get_or_create(username='Korben')
    return korben


def generate_signature(path, body, salt):
    """Generate the signature to be passed into the header."""

    message = bytes(path, 'utf-8') + body  + bytes(salt, 'utf-8')
    return sha256(message).hexdigest()
