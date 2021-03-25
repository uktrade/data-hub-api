import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.search.apps import get_search_app
from datahub.search.company.models import Company as ESCompany

pytestmark = pytest.mark.django_db


class TestCompanyElasticModel:
    """Test for the company elasticsearch model"""

    def test_company_dbmodel_to_dict(self, es):
        """Tests conversion of db model to dict."""
        company = CompanyFactory()
        app = get_search_app('company')
        company_qs = app.queryset.get(pk=company.pk)

        result = ESCompany.db_object_to_dict(company_qs)

        keys = {
            '_document_type',
            'archived',
            'archived_by',
            'archived_on',
            'archived_reason',
            'business_type',
            'company_number',
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
            'global_headquarters',
            'reference_code',
            'sector',
            'latest_interaction_date',

            'address',
            'registered_address',

            'one_list_group_global_account_manager',

            'trading_names',
            'turnover_range',
            'uk_based',
            'uk_region',
            'uk_address_postcode',
            'uk_registered_address_postcode',
            'vat_number',
            'duns_number',
            'website',
            'export_segment',
            'export_sub_segment',
        }

        assert set(result.keys()) == keys

    def test_company_dbmodels_to_es_documents(self, es):
        """Tests conversion of db models to Elasticsearch documents."""
        companies = CompanyFactory.create_batch(2)
        app = get_search_app('company')
        companies_qs = app.queryset.all()

        result = ESCompany.db_objects_to_es_documents(companies_qs)

        assert len(list(result)) == len(companies)
