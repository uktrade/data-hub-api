from collections import Counter

import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.search.company.models import Company as ESCompany, get_suggestions

pytestmark = pytest.mark.django_db


class TestCompanyElasticModel:
    """Test for the company elasticsearch model"""

    def test_company_dbmodel_to_dict(self, setup_es):
        """Tests conversion of db model to dict."""
        company = CompanyFactory()

        result = ESCompany.db_object_to_dict(company)

        keys = {
            'archived',
            'archived_by',
            'archived_on',
            'archived_reason',
            'business_type',
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
            'global_headquarters',
            'reference_code',
            'registered_address_1',
            'registered_address_2',
            'registered_address_country',
            'registered_address_county',
            'registered_address_postcode',
            'registered_address_town',
            'sector',
            'suggest',
            'trading_address_1',
            'trading_address_2',
            'trading_address_country',
            'trading_address_county',
            'trading_address_postcode',
            'trading_address_town',
            'trading_name',
            'trading_names',
            'turnover_range',
            'uk_based',
            'uk_region',
            'vat_number',
            'duns_number',
            'website',
        }

        assert set(result.keys()) == keys

    def test_company_dbmodels_to_es_documents(self, setup_es):
        """Tests conversion of db models to Elasticsearch documents."""
        companies = CompanyFactory.create_batch(2)

        result = ESCompany.db_objects_to_es_documents(companies)

        assert len(list(result)) == len(companies)

    @pytest.mark.parametrize(
        'name,alias,trading_names,archived,expected_suggestions',
        (
            (
                'Hello Hello uk',
                'Good Hello us',
                ['Trading Hello es', 'fr'],
                False,
                [
                    'Good', 'uk', 'Hello Hello uk', 'Trading Hello es',
                    'Trading', 'us', 'es', 'Good Hello us', 'fr', 'Hello',
                ],
            ),
            (
                'Hello      gb',
                None,
                [],
                False,
                ['Hello', 'gb', 'Hello      gb'],
            ),
            (
                'Hello      gb',
                None,
                [],
                True,
                [],
            ),

        ),
    )
    def test_company_get_suggestions(
        self,
        name,
        alias,
        trading_names,
        archived,
        expected_suggestions,
    ):
        """Test get an autocomplete search suggestions for a company"""
        db_company = CompanyFactory(
            name=name,
            alias=alias,
            trading_names=trading_names,
            archived=archived,
        )

        result = get_suggestions(db_company)

        assert Counter(result) == Counter(expected_suggestions)
