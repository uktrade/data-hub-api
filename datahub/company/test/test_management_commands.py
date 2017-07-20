import pytest
from django.core import management
from django.core.management import CommandError

from datahub.company.management.commands import manageusers
from datahub.company.test.factories import AdviserFactory


pytestmark = pytest.mark.django_db


def test_no_flag_passed_to_command():
    """Check one flag needs to get passed."""
    user1 = AdviserFactory(use_cdms_auth=False)
    user2 = AdviserFactory(use_cdms_auth=False)
    with pytest.raises(CommandError) as exception:
        management.call_command(manageusers.Command(), user1.email, user2.email)

    assert 'Pass either --enable or --disable' in str(exception.value)


def test_both_flags_passed_to_command():
    """Check only one flag needs to get passed."""
    user1 = AdviserFactory(use_cdms_auth=False)
    user2 = AdviserFactory(use_cdms_auth=False)
    with pytest.raises(CommandError) as exception:
        management.call_command(
            manageusers.Command(), user1.email, user2.email, '--enable', '--disable'
        )

    assert 'Pass either --enable or --disable not both' in str(exception.value)


def test_enable_users():
    """Check users get use_cdms_auth."""
    user1 = AdviserFactory(use_cdms_auth=False)
    user2 = AdviserFactory(use_cdms_auth=False)
    management.call_command(manageusers.Command(), user1.email, user2.email, '--enable')
    user1.refresh_from_db()
    user2.refresh_from_db()

    assert user1.use_cdms_auth
    assert user2.use_cdms_auth


def test_disable_users():
    """Check users get disabled."""
    user1 = AdviserFactory(use_cdms_auth=True)
    user2 = AdviserFactory(use_cdms_auth=True)
    management.call_command(manageusers.Command(), user1.email, user2.email, '--disable')
    user1.refresh_from_db()
    user2.refresh_from_db()

    assert user1.use_cdms_auth is False
    assert user2.use_cdms_auth is False
