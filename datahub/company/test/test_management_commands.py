import pytest
from django.core import management
from django.core.management import CommandError

from datahub.company.management.commands import manageusers
from datahub.company.test.factories import AdvisorFactory


pytestmark = pytest.mark.django_db


def test_no_flag_passed_to_command():
    """Check one flag needs to get passed."""
    user1 = AdvisorFactory(enabled=False)
    user2 = AdvisorFactory(enabled=False)
    with pytest.raises(CommandError) as exception:
        management.call_command(manageusers.Command(), user1.email, user2.email)

    assert 'Pass either --enable or --disable' in str(exception.value)


def test_both_flags_passed_to_command():
    """Check only one flag needs to get passed."""
    user1 = AdvisorFactory(enabled=False)
    user2 = AdvisorFactory(enabled=False)
    with pytest.raises(CommandError) as exception:
        management.call_command(manageusers.Command(), user1.email, user2.email, '--enable', '--disable')

    assert 'Pass either --enable or --disable not both' in str(exception.value)


def test_enable_users():
    """Check users get enabled."""
    user1 = AdvisorFactory(enabled=False)
    user2 = AdvisorFactory(enabled=False)
    management.call_command(manageusers.Command(), user1.email, user2.email, '--enable')
    user1.refresh_from_db()
    user2.refresh_from_db()

    assert user1.enabled
    assert user2.enabled


def test_disable_users():
    """Check users get disabled."""
    user1 = AdvisorFactory(enabled=True)
    user2 = AdvisorFactory(enabled=True)
    management.call_command(manageusers.Command(), user1.email, user2.email, '--disable')
    user1.refresh_from_db()
    user2.refresh_from_db()

    assert user1.enabled is False
    assert user2.enabled is False
