import pytest

from datahub.company.test.factories import (AdviserFactory, ContactFactory)
from datahub.core import constants
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.investment.validate import (
    get_incomplete_active_team_fields, get_incomplete_assign_pm_reqs_fields,
    get_incomplete_assign_pm_value_fields, get_incomplete_prospect_project_fields
)
from datahub.metadata.models import ReferralSourceActivity

pytestmark = pytest.mark.django_db


def test_validate_project_fail():
    """Tests validating an incomplete project section."""
    project = InvestmentProjectFactory(
        investment_type_id=constants.InvestmentType.fdi.value.id,
        fdi_type_id=None
    )
    errors = get_incomplete_prospect_project_fields(instance=project)
    assert errors == {
        'fdi_type': 'This field is required.'
    }


def test_validate_project_instance_success():
    """Tests validating a complete project section using a model instance."""
    project = InvestmentProjectFactory(
        client_contacts=[ContactFactory().id, ContactFactory().id]
    )
    errors = get_incomplete_prospect_project_fields(instance=project)
    assert not errors


def test_validate_non_fdi_type():
    """Tests non_fdi_type conditional validation."""
    investment_type_id = constants.InvestmentType.non_fdi.value.id
    project = InvestmentProjectFactory(
        investment_type_id=investment_type_id
    )
    errors = get_incomplete_prospect_project_fields(instance=project)
    assert 'non_fdi_type' in errors
    assert 'fdi_type' not in errors


def test_validate_fdi_type():
    """Tests fdi_type conditional validation."""
    investment_type_id = constants.InvestmentType.fdi.value.id
    project = InvestmentProjectFactory(
        investment_type_id=investment_type_id
    )
    errors = get_incomplete_prospect_project_fields(instance=project)
    assert 'fdi_type' in errors
    assert 'non_fdi_type' not in errors


def test_validate_project_referral_website():
    """Tests referral_source_activity_website conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.website.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_prospect_project_fields(instance=project)
    assert 'referral_source_activity_website' in errors
    assert 'referral_source_activity_event' not in errors
    assert 'referral_source_activity_marketing' not in errors


def test_validate_project_referral_event():
    """Tests referral_source_activity_event conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.event.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_prospect_project_fields(instance=project)
    assert 'referral_source_activity_event' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_marketing' not in errors


def test_validate_project_referral_marketing():
    """Tests referral_source_activity_marketing conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.marketing.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_prospect_project_fields(instance=project)
    assert 'referral_source_activity_marketing' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_event' not in errors


def test_validate_project_update_data():
    """Tests validation with update_data."""
    referral_source_id = constants.ReferralSourceActivity.marketing.value.id
    project = InvestmentProjectFactory()
    referral_source = ReferralSourceActivity.objects.get(pk=referral_source_id)
    update_data = {
        'referral_source_activity': referral_source
    }
    errors = get_incomplete_prospect_project_fields(instance=project,
                                                    update_data=update_data)
    assert 'referral_source_activity_marketing' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_event' not in errors


def test_validate_value_fail():
    """Tests validating an incomplete value section."""
    project = InvestmentProjectFactory(sector_id=None)
    errors = get_incomplete_assign_pm_value_fields(instance=project)
    assert errors == {
        'client_cannot_provide_total_investment': 'This field is required.',
        'total_investment': 'This field is required.',
        'number_new_jobs': 'This field is required.'
    }


def test_validate_value_instance_success():
    """Tests validating a complete value section using a model instance."""
    project = InvestmentProjectFactory(
        client_cannot_provide_total_investment=False,
        total_investment=100,
        number_new_jobs=0
    )
    errors = get_incomplete_assign_pm_value_fields(instance=project)
    assert not errors


def test_validate_reqs_fail():
    """Tests validating an incomplete reqs section."""
    project = InvestmentProjectFactory(sector_id=None)
    errors = get_incomplete_assign_pm_reqs_fields(instance=project)
    assert errors == {
        'client_considering_other_countries': 'This field is required.',
        'client_requirements': 'This field is required.',
        'site_decided': 'This field is required.',
        'strategic_drivers': 'This field is required.',
        'uk_region_locations': 'This field is required.'
    }


def test_validate_reqs_instance_success():
    """Tests validating a complete reqs section using a model instance."""
    strategic_drivers = [
        constants.InvestmentStrategicDriver.access_to_market.value.id
    ]
    uk_region_locations = [constants.UKRegion.england.value.id]
    project = InvestmentProjectFactory(
        client_considering_other_countries=False,
        client_requirements='client reqs',
        site_decided=False,
        strategic_drivers=strategic_drivers,
        uk_region_locations=uk_region_locations
    )
    errors = get_incomplete_assign_pm_reqs_fields(instance=project)
    assert not errors


def test_validate_reqs_competitor_countries_missing():
    """Tests missing competitor countries conditional validation."""
    project = InvestmentProjectFactory(
        client_considering_other_countries=True
    )
    errors = get_incomplete_assign_pm_reqs_fields(instance=project)
    assert 'competitor_countries' in errors


def test_validate_reqs_competitor_countries_present():
    """Tests required competitor countries conditional validation."""
    project = InvestmentProjectFactory(
        client_considering_other_countries=True,
        competitor_countries=[constants.Country.united_states.value.id]
    )
    errors = get_incomplete_assign_pm_reqs_fields(instance=project)
    assert 'competitor_countries' not in errors


def test_validate_team_fail():
    """Tests validating an incomplete team section."""
    project = InvestmentProjectFactory(sector_id=None)
    errors = get_incomplete_active_team_fields(instance=project)
    assert errors == {
        'project_assurance_adviser': 'This field is required.',
        'project_manager': 'This field is required.'
    }


def test_validate_team_instance_success():
    """Tests validating a complete team section using a model instance."""
    adviser = AdviserFactory()
    project = InvestmentProjectFactory(
        project_manager=adviser,
        project_assurance_adviser=adviser
    )
    errors = get_incomplete_active_team_fields(instance=project)
    assert not errors
