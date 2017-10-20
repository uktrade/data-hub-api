import pytest

from datahub.company.test.factories import CompanyFactory

from ..models import Company as ESCompany

pytestmark = pytest.mark.django_db


def test_company_dbmodel_to_dict(setup_es):
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


def test_company_dbmodels_to_es_documents(setup_es):
    """Tests conversion of db models to Elasticsearch documents."""
    companies = CompanyFactory.create_batch(2)

    result = ESCompany.dbmodels_to_es_documents(companies)

    assert len(list(result)) == len(companies)
