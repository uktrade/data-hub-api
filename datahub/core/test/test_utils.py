from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from datahub.core import constants
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
def test_valid_and_whitelisted_user(korben_auth_mock, settings):
    """Test valid result with valid creds and user and whitelisted."""
    user_model = get_user_model()
    user = user_model(
        first_name='Foo',
        last_name='Bar',
        email='foo@bar.com',
        date_joined=now(),
        is_active=False,
        dit_team_id=constants.Team.crm.value.id,
    )
    user.save(as_korben=True)
    settings.DIT_ENABLED_ADVISORS = ('foo@bar.com', )
    korben_auth_mock.return_value = True
    backend = CDMSUserBackend()

    result = backend.authenticate(username=user.email, password='assume_valid')
    korben_auth_mock.assert_called_with(username=user.email, password='assume_valid')

    assert str(result.pk) == str(user.pk)


@mock.patch('datahub.core.utils.CDMSUserBackend.korben_authenticate')
def test_valid_and_not_whitelisted_user(korben_auth_mock, settings):
    """Test valid result with valid creds and user but not whitelisted."""
    user_model = get_user_model()
    user = user_model(
        first_name='Foo',
        last_name='Bar',
        email='foo@bar.com',
        date_joined=now(),
        is_active=False,
        dit_team_id=constants.Team.crm.value.id,
    )
    user.save(as_korben=True)
    settings.DIT_ENABLED_ADVISORS = ()
    korben_auth_mock.return_value = True
    backend = CDMSUserBackend()

    result = backend.authenticate(username=user.email, password='assume_valid')
    korben_auth_mock.assert_called_with(username=user.email, password='assume_valid')

    assert result is None
