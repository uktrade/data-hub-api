import pytest

from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.core import constants
from datahub.investment.serializers import (
    IProjectRequirementsSerializer, IProjectSummarySerializer, IProjectTeamSerializer,
    IProjectValueSerializer
)
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.investment.validate import validate
from datahub.metadata.models import ReferralSourceActivity

pytestmark = pytest.mark.django_db


def test_validate_project_fail():
    """Tests validating an incomplete project section."""
    project = InvestmentProjectFactory(
        investment_type_id=constants.InvestmentType.fdi.value.id,
        fdi_type_id=None
    )
    errors = validate(instance=project, fields=IProjectSummarySerializer.Meta.fields)
    assert errors == {
        'fdi_type': 'This field is required.'
    }


def test_validate_project_instance_success():
    """Tests validating a complete project section using a model instance."""
    project = InvestmentProjectFactory(
        client_contacts=[ContactFactory().id, ContactFactory().id]
    )
    errors = validate(instance=project, fields=IProjectSummarySerializer.Meta.fields)
    assert not errors


def test_validate_non_fdi_type():
    """Tests non_fdi_type conditional validation."""
    investment_type_id = constants.InvestmentType.non_fdi.value.id
    project = InvestmentProjectFactory(
        investment_type_id=investment_type_id
    )
    errors = validate(instance=project, fields=IProjectSummarySerializer.Meta.fields)
    assert 'non_fdi_type' in errors
    assert 'fdi_type' not in errors


def test_validate_fdi_type():
    """Tests fdi_type conditional validation."""
    investment_type_id = constants.InvestmentType.fdi.value.id
    project = InvestmentProjectFactory(
        investment_type_id=investment_type_id
    )
    errors = validate(instance=project, fields=IProjectSummarySerializer.Meta.fields)
    assert 'fdi_type' in errors
    assert 'non_fdi_type' not in errors


def test_validate_business_activity_other_instance():
    """Tests other_business_activity conditional validation for a model instance."""
    project = InvestmentProjectFactory(
        business_activities=[constants.InvestmentBusinessActivity.other.value.id]
    )
    errors = validate(instance=project, fields=IProjectSummarySerializer.Meta.fields)
    assert errors == {
        'other_business_activity': 'This field is required.'
    }


def test_validate_business_activity_other_update_data():
    """Tests other_business_activity conditional validation for update data."""
    project = InvestmentProjectFactory()
    data = {
        'business_activities': [constants.InvestmentBusinessActivity.other.value.id]
    }
    errors = validate(instance=project, update_data=data,
                      fields=IProjectSummarySerializer.Meta.fields)
    assert errors == {
        'other_business_activity': 'This field is required.'
    }


def test_validate_project_referral_website():
    """Tests referral_source_activity_website conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.website.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = validate(instance=project, fields=IProjectSummarySerializer.Meta.fields)
    assert 'referral_source_activity_website' in errors
    assert 'referral_source_activity_event' not in errors
    assert 'referral_source_activity_marketing' not in errors


def test_validate_project_referral_event():
    """Tests referral_source_activity_event conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.event.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = validate(instance=project, fields=IProjectSummarySerializer.Meta.fields)
    assert 'referral_source_activity_event' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_marketing' not in errors


def test_validate_project_referral_marketing():
    """Tests referral_source_activity_marketing conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.marketing.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = validate(instance=project, fields=IProjectSummarySerializer.Meta.fields)
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
    errors = validate(instance=project, update_data=update_data,
                      fields=IProjectSummarySerializer.Meta.fields)
    assert 'referral_source_activity_marketing' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_event' not in errors


def test_validate_value_fail():
    """Tests validating an incomplete value section."""
    project = InvestmentProjectFactory(
        sector_id=None, stage_id=constants.InvestmentProjectStage.assign_pm.value.id
    )
    errors = validate(instance=project, fields=IProjectValueSerializer.Meta.fields)
    assert errors == {
        'client_cannot_provide_total_investment': 'This field is required.',
        'total_investment': 'This field is required.',
        'number_new_jobs': 'This field is required.'
    }


def test_validate_value_instance_success():
    """Tests validating a complete value section using a model instance."""
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.assign_pm.value.id,
        client_cannot_provide_total_investment=False,
        total_investment=100,
        number_new_jobs=0
    )
    errors = validate(instance=project, fields=IProjectValueSerializer.Meta.fields)
    assert not errors


def test_validate_reqs_fail():
    """Tests validating an incomplete reqs section."""
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.assign_pm.value.id,
        sector_id=None
    )
    errors = validate(instance=project, fields=IProjectRequirementsSerializer.Meta.fields)
    assert errors == {
        'client_considering_other_countries': 'This field is required.',
        'client_requirements': 'This field is required.',
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
        stage_id=constants.InvestmentProjectStage.assign_pm.value.id,
        client_considering_other_countries=False,
        client_requirements='client reqs',
        site_decided=False,
        strategic_drivers=strategic_drivers,
        uk_region_locations=uk_region_locations
    )
    errors = validate(instance=project, fields=IProjectRequirementsSerializer.Meta.fields)
    assert not errors


def test_validate_reqs_competitor_countries_missing():
    """Tests missing competitor countries conditional validation."""
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.assign_pm.value.id,
        client_considering_other_countries=True
    )
    errors = validate(instance=project, fields=IProjectRequirementsSerializer.Meta.fields)
    assert 'competitor_countries' in errors


def test_validate_reqs_competitor_countries_present():
    """Tests required competitor countries conditional validation."""
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.assign_pm.value.id,
        client_considering_other_countries=True,
        competitor_countries=[constants.Country.united_states.value.id]
    )
    errors = validate(instance=project, fields=IProjectRequirementsSerializer.Meta.fields)
    assert 'competitor_countries' not in errors


def test_validate_team_fail():
    """Tests validating an incomplete team section."""
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.active.value.id,
        sector_id=None
    )
    errors = validate(instance=project, fields=IProjectTeamSerializer.Meta.fields)
    assert errors == {
        'project_assurance_adviser': 'This field is required.',
        'project_manager': 'This field is required.'
    }


def test_validate_team_instance_success():
    """Tests validating a complete team section using a model instance."""
    adviser = AdviserFactory()
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.active.value.id,
        project_manager=adviser,
        project_assurance_adviser=adviser
    )
    errors = validate(instance=project, fields=IProjectTeamSerializer.Meta.fields)
    assert not errors


def test_validate_verify_win_instance_failure():
    """Tests validation for the verify win stage for an incomplete project instance."""
    adviser = AdviserFactory()
    strategic_drivers = [
        constants.InvestmentStrategicDriver.access_to_market.value.id
    ]
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.verify_win.value.id,
        client_contacts=[ContactFactory().id, ContactFactory().id],
        client_cannot_provide_total_investment=False,
        total_investment=100,
        number_new_jobs=10,
        client_considering_other_countries=False,
        client_requirements='client reqs',
        site_decided=False,
        strategic_drivers=strategic_drivers,
        uk_region_locations=[constants.UKRegion.england.value.id],
        project_assurance_adviser=adviser,
        project_manager=adviser
    )
    errors = validate(instance=project)
    assert errors == {
        'government_assistance': 'This field is required.',
        'number_safeguarded_jobs': 'This field is required.',
        'r_and_d_budget': 'This field is required.',
        'non_fdi_r_and_d_budget': 'This field is required.',
        'new_tech_to_uk': 'This field is required.',
        'export_revenue': 'This field is required.',
        'address_line_1': 'This field is required.',
        'address_line_2': 'This field is required.',
        'address_line_postcode': 'This field is required.',
        'average_salary': 'This field is required.',
        'client_cannot_provide_foreign_investment': 'This field is required.',
        'foreign_equity_investment': 'This field is required.',
    }


def test_validate_verify_win_instance_cond_validation():
    """Tests conditional validation for the verify win stage."""
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.verify_win.value.id,
        client_cannot_provide_total_investment=True,
        client_cannot_provide_foreign_investment=True,
        number_new_jobs=0
    )
    errors = validate(instance=project)
    assert 'total_investment' not in errors
    assert 'foreign_equity_investment' not in errors
    assert 'average_salary' not in errors


def test_validate_verify_win_instance_success():
    """Tests validation for the verify win stage for a complete project instance."""
    adviser = AdviserFactory()
    strategic_drivers = [
        constants.InvestmentStrategicDriver.access_to_market.value.id
    ]
    project = InvestmentProjectFactory(
        stage_id=constants.InvestmentProjectStage.verify_win.value.id,
        client_contacts=[ContactFactory().id, ContactFactory().id],
        client_cannot_provide_total_investment=False,
        total_investment=100,
        client_cannot_provide_foreign_investment=False,
        foreign_equity_investment=200,
        number_new_jobs=10,
        client_considering_other_countries=False,
        client_requirements='client reqs',
        site_decided=False,
        strategic_drivers=strategic_drivers,
        uk_region_locations=[constants.UKRegion.england.value.id],
        project_assurance_adviser=adviser,
        project_manager=adviser,
        government_assistance=False,
        number_safeguarded_jobs=0,
        r_and_d_budget=True,
        non_fdi_r_and_d_budget=True,
        new_tech_to_uk=True,
        export_revenue=True,
        address_line_1='12 London Road',
        address_line_2='London',
        address_line_postcode='SW1A 2AA',
        average_salary_id=constants.SalaryRange.below_25000.value.id
    )
    errors = validate(instance=project)
    assert not errors
