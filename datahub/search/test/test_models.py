import pytest

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.investment.test.factories import InvestmentProjectFactory

from ..company.models import Company as ESCompany
from ..contact.models import Contact as ESContact
from ..investment.models import InvestmentProject as ESInvestmentProject

pytestmark = pytest.mark.django_db


def test_company_dbmodel_to_dict():
    """Tests conversion of db model to dict."""
    company = CompanyFactory()

    result = ESCompany.dbmodel_to_dict(company)

    keys = {'business_type', 'registered_address_country',
            'sector', 'trading_address_country', 'uk_region',
            'contacts', 'id', 'uk_based', 'export_to_countries',
            'future_interest_countries', 'created_on',
            'modified_on', 'archived', 'archived_on',
            'archived_reason', 'archived_by', 'name',
            'registered_address_1', 'registered_address_2',
            'registered_address_town', 'registered_address_county',
            'registered_address_postcode', 'company_number', 'alias',
            'employee_range', 'turnover_range', 'account_manager',
            'description', 'website', 'trading_address_1',
            'trading_address_2', 'trading_address_town',
            'trading_address_county', 'trading_address_postcode',
            'headquarter_type', 'classification', 'parent',
            'one_list_account_owner'}

    assert set(result.keys()) == keys


def test_company_dbmodels_to_es_documents():
    """Tests conversion of db models to Elasticsearch documents."""
    companies = (CompanyFactory(), CompanyFactory(),)

    result = ESCompany.dbmodels_to_es_documents(companies)

    assert len(list(result)) == len(companies)


def test_contact_dbmodel_to_dict():
    """Tests conversion of db model to dict."""
    contact = ContactFactory()

    result = ESContact.dbmodel_to_dict(contact)

    keys = {'id', 'title', 'company', 'created_on',
            'modified_on', 'archived', 'archived_on',
            'archived_reason', 'archived_by', 'first_name',
            'last_name', 'job_title', 'adviser', 'primary',
            'telephone_countrycode', 'telephone_number',
            'email', 'address_same_as_company', 'address_1',
            'address_2', 'address_town', 'address_county',
            'address_country', 'address_postcode', 'telephone_alternative',
            'email_alternative', 'notes', 'contactable_by_dit',
            'contactable_by_dit_partners', 'contactable_by_email',
            'contactable_by_phone'}

    assert set(result.keys()) == keys


def test_contact_dbmodels_to_es_documents():
    """Tests conversion of db models to Elasticsearch documents."""
    contacts = (ContactFactory(), ContactFactory(),)

    result = ESContact.dbmodels_to_es_documents(contacts)

    assert len(list(result)) == len(contacts)


def test_investment_project_to_dict():
    """Tests conversion of db model to dict."""
    project = InvestmentProjectFactory()
    result = ESInvestmentProject.dbmodel_to_dict(project)

    keys = {'id', 'business_activities', 'client_contacts',
            'client_relationship_manager', 'investor_company',
            'investment_type', 'stage', 'referral_source_activity',
            'referral_source_adviser', 'sector', 'project_code',
            'created_on', 'modified_on', 'archived', 'archived_on',
            'archived_reason', 'archived_by', 'name', 'description',
            'nda_signed', 'estimated_land_date', 'project_shareable',
            'not_shareable_reason', 'actual_land_date',
            'approved_commitment_to_invest', 'approved_fdi',
            'approved_good_value', 'approved_high_value',
            'approved_landed', 'approved_non_fdi', 'intermediate_company',
            'referral_source_activity_website',
            'referral_source_activity_marketing',
            'referral_source_activity_event', 'fdi_type', 'fdi_value', 'non_fdi_type',
            'client_cannot_provide_total_investment', 'total_investment',
            'client_cannot_provide_foreign_investment',
            'foreign_equity_investment', 'government_assistance',
            'some_new_jobs', 'number_new_jobs', 'will_new_jobs_last_two_years',
            'average_salary', 'number_safeguarded_jobs', 'r_and_d_budget',
            'non_fdi_r_and_d_budget', 'new_tech_to_uk', 'export_revenue',
            'client_requirements', 'site_decided', 'address_line_1',
            'address_line_2', 'address_line_3', 'address_line_postcode',
            'uk_company_decided', 'uk_company', 'project_manager',
            'project_assurance_adviser', 'team_members', 'likelihood_of_landing',
            'priority', 'quotable_as_public_case_study', 'other_business_activity',
            'status', 'reason_delayed', 'reason_abandoned', 'date_abandoned',
            'reason_lost', 'date_lost', 'country_lost_to'}

    assert set(result.keys()) == keys


def test_investment_project_dbmodels_to_es_documents():
    """Tests conversion of db models to Elasticsearch documents."""
    projects = (InvestmentProjectFactory(), InvestmentProjectFactory(),)

    result = ESInvestmentProject.dbmodels_to_es_documents(projects)

    assert len(list(result)) == len(projects)
