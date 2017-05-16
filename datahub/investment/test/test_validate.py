import pytest

from datahub.company.test.factories import (AdvisorFactory, CompanyFactory,
                                            ContactFactory)
from datahub.core import constants
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.investment.validate import (
    get_incomplete_project_fields, get_incomplete_reqs_fields,
    get_incomplete_team_fields, get_incomplete_value_fields
)
from datahub.metadata.models import ReferralSourceActivity

pytestmark = pytest.mark.django_db


def test_validate_project_fail():
    """Tests validating an incomplete project section."""
    project = InvestmentProjectFactory(sector_id=None)
    errors = get_incomplete_project_fields(instance=project)
    assert errors == {
        'business_activities': 'This field is required.',
        'client_contacts': 'This field is required.',
        'client_relationship_manager': 'This field is required.',
        'fdi_type': 'This field is required.',
        'investor_company': 'This field is required.',
        'referral_source_activity': 'This field is required.',
        'referral_source_advisor': 'This field is required.',
        'sector': 'This field is required.'
    }


def test_validate_project_instance_success():
    """Tests validating a complete project section using a model instance."""
    advisor = AdvisorFactory()
    company = CompanyFactory()
    new_site_id = (constants.FDIType.creation_of_new_site_or_activity
                   .value.id)
    cold_call_id = constants.ReferralSourceActivity.cold_call.value.id
    investment_type_id = constants.InvestmentType.commitment_to_invest.value.id
    project = InvestmentProjectFactory(
        business_activities=[
            constants.InvestmentBusinessActivity.retail.value.id
        ],
        client_contacts=[ContactFactory().id, ContactFactory().id],
        client_relationship_manager_id=advisor.id,
        fdi_type_id=new_site_id,
        investment_type_id=investment_type_id,
        investor_company_id=company.id,
        referral_source_activity_id=cold_call_id,
        referral_source_advisor_id=advisor.id
    )
    errors = get_incomplete_project_fields(instance=project)
    assert not errors


def test_validate_non_fdi_type():
    """Tests non_fdi_type conditional validation."""
    investment_type_id = constants.InvestmentType.non_fdi.value.id
    project = InvestmentProjectFactory(
        investment_type_id=investment_type_id
    )
    errors = get_incomplete_project_fields(instance=project)
    assert 'non_fdi_type' in errors
    assert 'fdi_type' not in errors


def test_validate_fdi_type():
    """Tests fdi_type conditional validation."""
    investment_type_id = constants.InvestmentType.fdi.value.id
    project = InvestmentProjectFactory(
        investment_type_id=investment_type_id
    )
    errors = get_incomplete_project_fields(instance=project)
    assert 'fdi_type' in errors
    assert 'non_fdi_type' not in errors


def test_validate_project_referral_website():
    """Tests referral_source_activity_website conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.website.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_project_fields(instance=project)
    assert 'referral_source_activity_website' in errors
    assert 'referral_source_activity_event' not in errors
    assert 'referral_source_activity_marketing' not in errors


def test_validate_project_referral_event():
    """Tests referral_source_activity_event conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.event.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_project_fields(instance=project)
    assert 'referral_source_activity_event' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_marketing' not in errors


def test_validate_project_referral_marketing():
    """Tests referral_source_activity_marketing conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.marketing.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_project_fields(instance=project)
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
    errors = get_incomplete_project_fields(instance=project,
                                           update_data=update_data)
    assert 'referral_source_activity_marketing' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_event' not in errors


def test_validate_value_fail():
    """Tests validating an incomplete value section."""
    project = InvestmentProjectFactory(sector_id=None)
    errors = get_incomplete_value_fields(instance=project)
    assert errors == {
        'client_cannot_provide_foreign_investment': 'This field is required.',
        'client_cannot_provide_total_investment': 'This field is required.',
        'export_revenue': 'This field is required.',
        'foreign_equity_investment': 'This field is required.',
        'government_assistance': 'This field is required.',
        'new_tech_to_uk': 'This field is required.',
        'non_fdi_r_and_d_budget': 'This field is required.',
        'number_new_jobs': 'This field is required.',
        'number_safeguarded_jobs': 'This field is required.',
        'r_and_d_budget': 'This field is required.',
        'total_investment': 'This field is required.'
    }


def test_validate_value_instance_success():
    """Tests validating a complete value section using a model instance."""
    project = InvestmentProjectFactory(
        client_cannot_provide_foreign_investment=False,
        client_cannot_provide_total_investment=False,
        total_investment=100,
        foreign_equity_investment=100,
        government_assistance=True,
        number_new_jobs=0,
        number_safeguarded_jobs=0,
        r_and_d_budget=False,
        non_fdi_r_and_d_budget=False,
        new_tech_to_uk=False,
        export_revenue=True
    )
    errors = get_incomplete_value_fields(instance=project)
    assert not errors


def test_validate_average_salary_required_missing():
    """Tests average salary conditional validation."""
    # average_salary_id = constants.AverageSalary.below_25000.value.id
    project = InvestmentProjectFactory(number_new_jobs=100)
    errors = get_incomplete_value_fields(instance=project)
    assert 'average_salary' in errors


def test_validate_average_salary_required_present():
    """Tests average salary conditional validation."""
    average_salary_id = constants.SalaryRange.below_25000.value.id
    project = InvestmentProjectFactory(
        number_new_jobs=100, average_salary_id=average_salary_id
    )
    errors = get_incomplete_value_fields(instance=project)
    assert 'average_salary' not in errors


def test_validate_reqs_fail():
    """Tests validating an incomplete reqs section."""
    project = InvestmentProjectFactory(sector_id=None)
    errors = get_incomplete_reqs_fields(instance=project)
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
    errors = get_incomplete_reqs_fields(instance=project)
    assert not errors


def test_validate_reqs_competitor_countries_missing():
    """Tests missing competitor countries conditional validation."""
    project = InvestmentProjectFactory(
        client_considering_other_countries=True
    )
    errors = get_incomplete_reqs_fields(instance=project)
    assert 'competitor_countries' in errors


def test_validate_reqs_competitor_countries_present():
    """Tests required competitor countries conditional validation."""
    project = InvestmentProjectFactory(
        client_considering_other_countries=True,
        competitor_countries=[constants.Country.united_states.value.id]
    )
    errors = get_incomplete_reqs_fields(instance=project)
    assert 'competitor_countries' not in errors


def test_validate_team_fail():
    """Tests validating an incomplete team section."""
    project = InvestmentProjectFactory(sector_id=None)
    errors = get_incomplete_team_fields(instance=project)
    assert errors == {
        'project_assurance_advisor': 'This field is required.',
        'project_manager': 'This field is required.'
    }


def test_validate_team_instance_success():
    """Tests validating a complete team section using a model instance."""
    advisor = AdvisorFactory()
    project = InvestmentProjectFactory(
        project_manager=advisor,
        project_assurance_advisor=advisor
    )
    errors = get_incomplete_team_fields(instance=project)
    assert not errors
