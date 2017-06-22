from unittest import mock

import pytest

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.search import models

pytestmark = pytest.mark.django_db


def test_id_name_dict():
    """Tests _id_name_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.name = 'test'

    res = models._id_name_dict(obj)

    assert res == {
        'id': str(obj.id),
        'name': obj.name,
    }


def test_id_type_dict():
    """Tests _id_type_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.type = 'test'

    res = models._id_type_dict(obj)

    assert res == {
        'id': str(obj.id),
        'type': obj.type,
    }


def test_id_uri_dict():
    """Tests _id_type_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.uri = 'test'

    res = models._id_uri_dict(obj)

    assert res == {
        'id': str(obj.id),
        'uri': obj.uri,
    }


def test_contact_dict():
    """Tests contact_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.first_name = 'First'
    obj.last_name = 'Last'

    res = models._contact_dict(obj)

    assert res == {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
    }


def test_company_dict():
    """Tests company_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.company_number = '01234567'

    res = models._company_dict(obj)

    assert res == {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }


def test_company_dbmodel_to_dict():
    """Tests conversion of db model to dict."""
    company = CompanyFactory()

    result = models.Company.dbmodel_to_dict(company)

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

    result = models.Company.dbmodels_to_es_documents(companies)

    assert len(list(result)) == len(companies)


def test_contact_dbmodel_to_dict():
    """Tests conversion of db model to dict."""
    contact = ContactFactory()

    result = models.Contact.dbmodel_to_dict(contact)

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

    result = models.Contact.dbmodels_to_es_documents(contacts)

    assert len(list(result)) == len(contacts)


def test_investment_project_to_dict():
    """Tests conversion of db model to dict."""
    project = InvestmentProjectFactory()
    result = models.InvestmentProject.dbmodel_to_dict(project)

    keys = {'id', 'business_activities', 'client_contacts',
            'client_relationship_manager', 'investor_company',
            'investment_type', 'phase', 'referral_source_activity',
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
            'referral_source_activity_event', 'fdi_type', 'non_fdi_type',
            'client_cannot_provide_total_investment', 'total_investment',
            'client_cannot_provide_foreign_investment',
            'foreign_equity_investment', 'government_assistance',
            'number_new_jobs', 'average_salary',
            'number_safeguarded_jobs', 'r_and_d_budget',
            'non_fdi_r_and_d_budget', 'new_tech_to_uk', 'export_revenue',
            'client_requirements', 'site_decided', 'address_line_1',
            'address_line_2', 'address_line_3', 'address_line_postcode',
            'uk_company', 'project_manager', 'project_assurance_adviser'}

    assert set(result.keys()) == keys


def test_investment_project_dbmodels_to_es_documents():
    """Tests conversion of db models to Elasticsearch documents."""
    projects = (InvestmentProjectFactory(), InvestmentProjectFactory(),)

    result = models.InvestmentProject.dbmodels_to_es_documents(projects)

    assert len(list(result)) == len(projects)
