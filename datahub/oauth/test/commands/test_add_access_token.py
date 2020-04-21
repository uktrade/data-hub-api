import re
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.core.management import call_command, CommandError
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory
from datahub.oauth.management.commands import add_access_token


@pytest.mark.django_db
@pytest.mark.usefixtures('local_memory_cache')
class TestAddAccessTokenCommand:
    """Tests for the add_access_token management command."""

    def test_fails_when_adviser_doesnt_exist(self):
        """The command should fail when if there is no adviser with the specified email address."""
        command = add_access_token.Command()

        with pytest.raises(CommandError) as excinfo:
            call_command(command, 'test@test.invalid')

        assert str(excinfo.value) == 'No adviser with SSO email user ID test@test.invalid found.'

    @pytest.mark.parametrize(
        'command_kwargs,expected_timeout',
        (
            # Default timeout
            ({}, timedelta(hours=10)),
            # With custom timeout
            ({'hours': 1}, timedelta(hours=1)),
        ),
    )
    def test_adds_access_token_to_cache(self, command_kwargs, expected_timeout):
        """The command should add the generated access token to the cache."""
        sso_email_user_id = 'id@datahub.test'
        adviser = AdviserFactory(sso_email_user_id=sso_email_user_id)

        command = add_access_token.Command()

        frozen_time = now()
        with freeze_time(frozen_time):
            success_message = call_command(command, sso_email_user_id, **command_kwargs)

        match = re.search(r'token (?P<token>[0-9a-zA-Z_-]+) ', success_message)
        assert match

        token = match.group('token')
        expected_expiry_time = frozen_time + expected_timeout

        with freeze_time(expected_expiry_time - timedelta(seconds=1)):
            assert cache.get(f'access_token:{token}') == {
                'email': adviser.email,
                'sso_email_user_id': sso_email_user_id,
            }

        with freeze_time(expected_expiry_time):
            assert cache.get(f'access_token:{token}') is None

    def test_can_use_custom_token(self):
        """
        It should be possible to use a custom access token (instead of an auto-generated
        one).
        """
        sso_email_user_id = 'id@datahub.test'
        token = 'test-token'
        adviser = AdviserFactory(sso_email_user_id=sso_email_user_id)

        command = add_access_token.Command()

        frozen_time = now()
        with freeze_time(frozen_time):
            call_command(command, sso_email_user_id, token=token)

            assert cache.get(f'access_token:{token}') == {
                'email': adviser.email,
                'sso_email_user_id': sso_email_user_id,
            }
