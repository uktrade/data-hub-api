from unittest import mock

import pytest
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed

from datahub.korben.authentication import KorbenSharedSecretAuthentication
from datahub.korben.utils import get_korben_user

pytestmark = pytest.mark.django_db  # use db


@mock.patch('datahub.korben.authentication.generate_signature')
def test_successful_authentication(mocked_generate_signature):
    """Korben successfully authenticates."""
    mocked_generate_signature.return_value = '123'
    request = RequestFactory()
    request = request.get('foobar', HTTP_X_SIGNATURE='123')
    result, _ = KorbenSharedSecretAuthentication().authenticate(request)
    assert result == get_korben_user()


@mock.patch('datahub.korben.authentication.generate_signature')
def test_not_attempted_authentication(mocked_generate_signature):
    """Authentication not attempted."""
    mocked_generate_signature.return_value = '123'
    request = RequestFactory()
    request = request.get('foobar')
    result = KorbenSharedSecretAuthentication().authenticate(request)
    assert result is None


@mock.patch('datahub.korben.authentication.generate_signature')
def test_unsuccessful_authentication(mocked_generate_signature):
    """Korben unsuccessfully authenticates."""
    mocked_generate_signature.return_value = '123'
    request = RequestFactory()
    request = request.get('foobar', HTTP_X_SIGNATURE='567')
    with pytest.raises(AuthenticationFailed, message='Shared secret authentication failed'):
        KorbenSharedSecretAuthentication().authenticate(request)
