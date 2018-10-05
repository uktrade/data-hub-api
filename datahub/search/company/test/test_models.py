import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.search.company.models import Company as ESCompany

pytestmark = pytest.mark.django_db


def test_company_dbmodel_to_dict(setup_es):
    """Tests conversion of db model to dict."""
    company = CompanyFactory()

    result = ESCompany.db_object_to_dict(company)

    keys = {
        'archived',
        'archived_by',
        'archived_on',
        'archived_reason',
        'business_type',
        'classification',
        'companies_house_data',
        'company_number',
        'contacts',
        'created_on',
        'description',
        'employee_range',
        'export_experience_category',
        'export_to_countries',
        'future_interest_countries',
        'headquarter_type',
        'id',
        'modified_on',
        'name',
        'one_list_account_owner',
        'global_headquarters',
        'reference_code',
        'registered_address_1',
        'registered_address_2',
        'registered_address_country',
        'registered_address_county',
        'registered_address_postcode',
        'registered_address_town',
        'sector',
        'trading_address_1',
        'trading_address_2',
        'trading_address_country',
        'trading_address_county',
        'trading_address_postcode',
        'trading_address_town',
        'trading_name',
        'turnover_range',
        'uk_based',
        'uk_region',
        'vat_number',
        'website',
    }

    assert set(result.keys()) == keys


def test_company_dbmodels_to_es_documents(setup_es):
    """Tests conversion of db models to Elasticsearch documents."""
    companies = CompanyFactory.create_batch(2)

    result = ESCompany.db_objects_to_es_documents(companies)

    assert len(list(result)) == len(companies)
