from collections import Counter

import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import Country as CountryConstant
from datahub.search.company.models import Company as ESCompany, get_suggestions

pytestmark = pytest.mark.django_db


class TestCompanyElasticModel:
    """Test for the company elasticsearch model"""

    def test_company_dbmodel_to_dict(self, es):
        """Tests conversion of db model to dict."""
        company = CompanyFactory()

        result = ESCompany.db_object_to_dict(company)

        keys = {
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
            'suggest',

            'address',
            'registered_address',

            'one_list_group_global_account_manager',

            'trading_names',
            'turnover_range',
            'uk_based',
            'uk_region',
            'vat_number',
            'duns_number',
            'website',
        }

        assert set(result.keys()) == keys

    def test_company_dbmodels_to_es_documents(self, es):
        """Tests conversion of db models to Elasticsearch documents."""
        companies = CompanyFactory.create_batch(2)

        result = ESCompany.db_objects_to_es_documents(companies)

        assert len(list(result)) == len(companies)

    @pytest.mark.parametrize(
        'name,trading_names,archived,registered_address_country,'
        'expected_input_suggestions,expected_contexts',
        (
            (
                'Hello Hello uk',
                ['Good Hello us', 'fr'],
                False,
                CountryConstant.united_kingdom.value.id,
                [
                    'Good', 'uk', 'Hello Hello uk',
                    'us', 'Good Hello us', 'fr', 'Hello',
                ],
                [
                    CountryConstant.united_kingdom.value.id,
                ],
            ),
            (
                'Hello      gb',
                [],
                False,
                CountryConstant.canada.value.id,
                ['Hello', 'gb', 'Hello      gb'],
                [
                    CountryConstant.canada.value.id,
                    CountryConstant.united_kingdom.value.id,
                ],
            ),
            (
                'Hello      gb',
                [],
                True,
                CountryConstant.united_kingdom.value.id,
                {},
                [],
            ),
        ),
    )
    def test_company_get_suggestions(
        self,
        name,
        trading_names,
        archived,
        registered_address_country,
        expected_input_suggestions,
        expected_contexts,
    ):
        """Test get an autocomplete search suggestions for a company"""
        db_company = CompanyFactory(
            name=name,
            trading_names=trading_names,
            archived=archived,
            registered_address_country_id=registered_address_country,
            address_country_id=CountryConstant.united_kingdom.value.id,
        )

        result = get_suggestions(db_company)
        if result:
            assert Counter(result['input']) == Counter(expected_input_suggestions)
            assert 'country' in result['contexts']
            assert Counter(result['contexts']['country']) == Counter(expected_contexts)

        else:
            assert Counter(result) == Counter(expected_input_suggestions)
