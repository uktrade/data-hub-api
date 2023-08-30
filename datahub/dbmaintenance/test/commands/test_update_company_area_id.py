import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory

pytestmark = pytest.mark.django_db


def test_successful_update_area_id():
    """Test successful address_area_id update."""
    company = CompanyFactory(
        address_area_id='c35c119a-bc4d-4e48-9ace-167dbe8cb695',
        address_country_id='80756b9a-5d95-e211-a939-e4115bead28a',
    )
    call_command(
        'update_company_area_id',
        'c35c119a-bc4d-4e48-9ace-167dbe8cb695',
        '80756b9a-5d95-e211-a939-e4115bead28a',
    )
    company.refresh_from_db()
    assert company.address_area_id is None


def test_no_update_needed_area_id():
    """Test that no changes are made if the address_area_id is already None."""
    company = CompanyFactory(
        address_area_id=None,
        address_country_id='80756b9a-5d95-e211-a939-e4115bead28a',
    )
    call_command(
        'update_company_area_id',
        'c35c119a-bc4d-4e48-9ace-167dbe8cb695',
        '80756b9a-5d95-e211-a939-e4115bead28a',
    )
    company.refresh_from_db()
    assert company.address_area_id is None

    versions = Version.objects.get_for_object(company)
    assert versions.count() == 0


def test_no_company_with_given_country_id():
    """Test that no changes are made if no company matches the given address_country_id."""
    company = CompanyFactory(
        address_area_id='c35c119a-bc4d-4e48-9ace-167dbe8cb695',
        address_country_id='80756b9a-5d95-e211-a939-e4115bead28a',
    )
    call_command(
        'update_company_area_id',
        'c35c119a-bc4d-4e48-9ace-167dbe8cb695',
        'dcba4321-dcba-4321-dcba-0987654321dc',
    )
    company.refresh_from_db()
    assert str(company.address_area_id) == 'c35c119a-bc4d-4e48-9ace-167dbe8cb695'

    versions = Version.objects.get_for_object(company)
    assert versions.count() == 0
