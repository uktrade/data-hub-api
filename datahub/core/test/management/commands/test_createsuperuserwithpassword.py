from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management import CommandError

User = get_user_model()


@pytest.mark.django_db
class TestCreatesuperuserwithpassword:
    """
    Test createsuperuserwithpassword django management command.
    """

    def test_command_successful(self):
        """
        Test that calling the command gives an expected message when successful.
        """
        out = StringIO()
        username = 'test-user'
        call_command('createsuperuserwithpassword', username, 'foobar', stdout=out)
        assert 'Successfully created user' in out.getvalue()
        user = User.objects.get(email=username)
        assert user.is_superuser

    def test_command_failure(self):
        """
        Test that calling the command gives an expected message when unsuccessful.
        """
        username = 'test-user'
        # Create superuser initially
        call_command('createsuperuserwithpassword', username, 'foobar')
        out = StringIO()
        # Assert that second call fails as expected
        with pytest.raises(CommandError):
            call_command('createsuperuserwithpassword', username, 'foobar', stdout=out)
