import pytest
from django.core import management

from datahub.company.management.commands import enableusers
from datahub.company.test.factories import AdvisorFactory


pytestmark = pytest.mark.django_db


def test_enable_users():
    """Check users get enabled."""
    user1 = AdvisorFactory(enabled=False)
    user2 = AdvisorFactory(enabled=False)
    management.call_command(enableusers.Command(), user1.email, user2.email)
    user1.refresh_from_db()
    user2.refresh_from_db()
    assert user1.enabled
    assert user2.enabled


def test_disable_users():
    """Check users get disabled."""
    user1 = AdvisorFactory(enabled=True)
    user2 = AdvisorFactory(enabled=True)
    management.call_command(enableusers.Command(), user1.email, user2.email, '--disable')
    user1.refresh_from_db()
    user2.refresh_from_db()
    assert user1.enabled is False
    assert user2.enabled is False
