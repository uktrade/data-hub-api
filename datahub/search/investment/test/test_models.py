import pytest

from datahub.investment.test.factories import InvestmentProjectFactory

from ..models import InvestmentProject as ESInvestmentProject

pytestmark = pytest.mark.django_db


def test_investment_project_to_dict(setup_es):
    """Tests conversion of db model to dict."""
    project = InvestmentProjectFactory()
    result = ESInvestmentProject.dbmodel_to_dict(project)

    keys = {
        'id',
        'business_activities',
        'client_contacts',
        'client_relationship_manager',
        'investor_company',
        'investor_company_country',
        'investor_type',
        'level_of_involvement',
        'investment_type',
        'stage',
        'referral_source_activity',
        'referral_source_adviser',
        'sector',
        'project_code',
        'created_on',
        'created_by',
        'modified_on',
        'archived',
        'archived_on',
        'archived_reason',
        'archived_by',
        'name',
        'description',
        'comments',
        'anonymous_description',
        'estimated_land_date',
        'actual_land_date',
        'approved_commitment_to_invest',
        'approved_fdi',
        'approved_good_value',
        'approved_high_value',
        'approved_landed',
        'approved_non_fdi',
        'intermediate_company',
        'referral_source_activity_website',
        'referral_source_activity_marketing',
        'referral_source_activity_event',
        'fdi_type',
        'fdi_value',
        'client_cannot_provide_total_investment',
        'total_investment',
        'client_cannot_provide_foreign_investment',
        'foreign_equity_investment',
        'government_assistance',
        'some_new_jobs',
        'specific_programme',
        'number_new_jobs',
        'will_new_jobs_last_two_years',
        'average_salary',
        'number_safeguarded_jobs',
        'r_and_d_budget',
        'non_fdi_r_and_d_budget',
        'associated_non_fdi_r_and_d_project',
        'new_tech_to_uk',
        'export_revenue',
        'client_requirements',
        'uk_region_locations',
        'actual_uk_regions',
        'site_decided',
        'address_1',
        'address_2',
        'address_town',
        'address_postcode',
        'uk_company_decided',
        'uk_company',
        'project_manager',
        'project_assurance_adviser',
        'team_members',
        'likelihood_of_landing',
        'priority',
        'quotable_as_public_case_study',
        'other_business_activity',
        'status',
        'reason_delayed',
        'reason_abandoned',
        'date_abandoned',
        'reason_lost',
        'date_lost',
        'country_lost_to',
    }

    assert set(result.keys()) == keys


def test_investment_project_dbmodels_to_es_documents(setup_es):
    """Tests conversion of db models to Elasticsearch documents."""
    projects = InvestmentProjectFactory.create_batch(2)

    result = ESInvestmentProject.dbmodels_to_es_documents(projects)

    assert len(list(result)) == len(projects)
