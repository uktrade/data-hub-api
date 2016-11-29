from unittest import mock

import pytest

from datahub.core.test_utils import get_test_user
from datahub.core.utils import CDMSUserBackend


pytestmark = pytest.mark.django_db  # use db


@mock.patch('datahub.core.utils.CDMSUserBackend.korben_authenticate')
def test_invalid_credentials(korben_auth_mock):
    """Test empty result with invalid credentials."""
    korben_auth_mock.return_value = False
    backend = CDMSUserBackend()

    assert backend.authenticate(username='invalid', password='invalid') is None
    assert korben_auth_mock.called is False


@mock.patch('datahub.core.utils.CDMSUserBackend.korben_authenticate')
def test_invalid_credentials_with_valid_user(korben_auth_mock):
    """Test empty result with invalid password for valid user."""
    user = get_test_user()
    korben_auth_mock.return_value = False
    backend = CDMSUserBackend()

    assert backend.authenticate(username=user.email, password='invalid') is None
    korben_auth_mock.assert_called_with(username=user.email, password='invalid')


@mock.patch('datahub.core.utils.CDMSUserBackend.korben_authenticate')
def test_valid_user(korben_auth_mock):
    """Test valid result with valid creds and user."""
    user = get_test_user()
    korben_auth_mock.return_value = True
    backend = CDMSUserBackend()

    result = backend.authenticate(username=user.email, password='assume_valid')
    korben_auth_mock.assert_called_with(username=user.email, password='assume_valid')

    assert str(result.pk) == user.pk
