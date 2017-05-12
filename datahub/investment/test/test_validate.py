import pytest

from datahub.company.test.factories import (AdvisorFactory, CompanyFactory,
                                            ContactFactory)
from datahub.core import constants
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.investment.validate import get_incomplete_project_fields

pytestmark = pytest.mark.django_db


def test_validate_project_fail():
    """Tests validating an incomplete project section."""
    project = InvestmentProjectFactory(sector_id=None)
    errors = get_incomplete_project_fields(project)
    assert errors == {
        'business_activity': 'This field is required.',
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
        business_activity=[
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
    errors = get_incomplete_project_fields(project)
    assert not errors


def test_validate_non_fdi_type():
    """Tests non_fdi_type conditional validation."""
    investment_type_id = constants.InvestmentType.non_fdi.value.id
    project = InvestmentProjectFactory(
        investment_type_id=investment_type_id
    )
    errors = get_incomplete_project_fields(project)
    assert 'non_fdi_type' in errors
    assert 'fdi_type' not in errors


def test_validate_fdi_type():
    """Tests fdi_type conditional validation."""
    investment_type_id = constants.InvestmentType.fdi.value.id
    project = InvestmentProjectFactory(
        investment_type_id=investment_type_id
    )
    errors = get_incomplete_project_fields(project)
    assert 'fdi_type' in errors
    assert 'non_fdi_type' not in errors


def test_validate_project_referral_website():
    """Tests referral_source_activity_website conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.website.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_project_fields(project)
    assert 'referral_source_activity_website' in errors
    assert 'referral_source_activity_event' not in errors
    assert 'referral_source_activity_marketing' not in errors


def test_validate_project_referral_event():
    """Tests referral_source_activity_event conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.event.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_project_fields(project)
    assert 'referral_source_activity_event' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_marketing' not in errors


def test_validate_project_referral_marketing():
    """Tests referral_source_activity_marketing conditional validation."""
    referral_source_id = constants.ReferralSourceActivity.marketing.value.id
    project = InvestmentProjectFactory(
        referral_source_activity_id=referral_source_id
    )
    errors = get_incomplete_project_fields(project)
    assert 'referral_source_activity_marketing' in errors
    assert 'referral_source_activity_website' not in errors
    assert 'referral_source_activity_event' not in errors
