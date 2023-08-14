import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory

pytestmark = pytest.mark.django_db


def test_successful_update():
    """Test successful export_potential update."""
    company = CompanyFactory(export_potential=Company.ExportPotentialScore.LOW)
    call_command('update_single_company_export_potential', company.id, 'high')
    company.refresh_from_db()
    assert company.export_potential == Company.ExportPotentialScore.HIGH

    versions = Version.objects.get_for_object(company)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Export potential updated via management command.'


def test_simulate_update():
    """Test that the --simulate flag doesn't make any actual updates."""
    company = CompanyFactory(export_potential=Company.ExportPotentialScore.LOW)
    call_command('update_single_company_export_potential', company.id, 'high', simulate=True)
    company.refresh_from_db()
    assert company.export_potential == Company.ExportPotentialScore.LOW
    versions = Version.objects.get_for_object(company)
    assert versions.count() == 0


def test_no_update_needed():
    """Test that no changes are made if the company already has the desired export potential."""
    company = CompanyFactory(export_potential=Company.ExportPotentialScore.HIGH)
    call_command('update_single_company_export_potential', company.id, 'high')
    company.refresh_from_db()
    assert company.export_potential == Company.ExportPotentialScore.HIGH
    versions = Version.objects.get_for_object(company)
    assert versions.count() == 0


def test_invalid_export_propensity():
    """Test that command raises error for invalid export propensity."""
    company = CompanyFactory(export_potential=Company.ExportPotentialScore.LOW)
    with pytest.raises(CommandError, match='Invalid export_propensity value'):
        call_command('update_single_company_export_potential', company.id, 'INVALID')
