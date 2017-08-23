import pytest

from django.core.management import call_command

from ..models import Market

pytestmark = pytest.mark.django_db


def test_with_empty_table():
    """Test that if the table is empty the command loads all the records."""
    Market.objects.all().delete()

    call_command('load_initial_omis_markets')

    assert Market.objects.count() > 0


def test_with_existing_records():
    """Test that if the table is not empty, the command doesn't do anything."""
    assert Market.objects.count() > 0

    market = Market.objects.first()
    market.manager_email = 'example@example.com'
    market.save()

    call_command('load_initial_omis_markets')

    market.refresh_from_db()
    assert market.manager_email == 'example@example.com'


def test_with_override_flag():
    """
    Test that if the table is not empty and the override flag is specified, the
    command loads all the records anyway.
    """
    assert Market.objects.count() > 0

    market = Market.objects.first()
    previous_manager_email = market.manager_email

    market.manager_email = 'example@example.com'
    market.save()

    call_command('load_initial_omis_markets', '--override')

    market.refresh_from_db()
    assert market.manager_email != 'example@example.com'
    assert market.manager_email == previous_manager_email
