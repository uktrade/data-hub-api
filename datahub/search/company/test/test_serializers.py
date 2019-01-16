import pytest
from elasticsearch_dsl.utils import AttrDict

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.search.company.models import Company as ESCompany
from datahub.search.company.serializers import AutocompleteSearchCompanySerializer


pytestmark = pytest.mark.django_db


class TestAutocompleteSearchCompanySerializer:
    """Tests for the autocomplete search company serializer."""

    def test_serializer_uses_source_if_present(self):
        """
        Tests the serializer can handle the data object within a
        _source parameter as this is how elasticsearch returns the documents.
        """
        company = CompanyFactory(
            name='Company name 1',
            trading_names=['trading name 1', 'trading name 2'],
        )
        elasticsearch_company_dict = ESCompany.es_document(company)

        assert '_source' in elasticsearch_company_dict
        assert 'id' not in elasticsearch_company_dict
        assert 'id' in elasticsearch_company_dict['_source']

        serializer = AutocompleteSearchCompanySerializer(
            AttrDict(elasticsearch_company_dict),
        )
        assert serializer.data['id'] == str(company.id)
        assert serializer.data['name'] == company.name
        assert serializer.data['trading_name'] == company.trading_names[0]
        assert serializer.data['trading_names'] == company.trading_names

    def test_serializer_without_source(self):
        """
        Tests the serializer can handle data not within a _source parameter
        """
        company = CompanyFactory(
            name='Company name 1',
            trading_names=['trading name 1', 'trading name 2'],
        )
        elasticsearch_company_dict = ESCompany.db_object_to_dict(company)

        assert '_source' not in elasticsearch_company_dict
        assert 'id' in elasticsearch_company_dict

        serializer = AutocompleteSearchCompanySerializer(
            AttrDict(elasticsearch_company_dict),
        )
        assert serializer.data['id'] == str(company.id)
        assert serializer.data['name'] == company.name
        assert serializer.data['trading_name'] == company.trading_names[0]
        assert serializer.data['trading_names'] == company.trading_names

    def test_serializer_returns_trading_and_registered_addresses(self):
        """Tests the serializer returns both the trading and registered addresses."""
        company = CompanyFactory(
            trading_address_1='Trading address 1',
            trading_address_2='Trading address 2',
            trading_address_town='Trading address town',
            trading_address_county='Trading address county',
            trading_address_country_id=constants.Country.ireland.value.id,
            trading_address_postcode='TR12DI',
            registered_address_1='Registered address 1',
            registered_address_2='Registered address 2',
            registered_address_town='Registered address town',
            registered_address_county='Registered address county',
            registered_address_country_id=constants.Country.japan.value.id,
            registered_address_postcode='RE12DI',
        )

        elasticsearch_company_dict = ESCompany.es_document(company)
        serializer = AutocompleteSearchCompanySerializer(
            AttrDict(elasticsearch_company_dict),
        )
        data = serializer.data

        assert data['trading_address_1'] == company.trading_address_1
        assert data['trading_address_2'] == company.trading_address_2
        assert data['trading_address_town'] == company.trading_address_town
        assert data['trading_address_county'] == company.trading_address_county
        assert data['trading_address_postcode'] == company.trading_address_postcode
        assert data['trading_address_country']['name'] == company.trading_address_country.name

        assert data['registered_address_1'] == company.registered_address_1
        assert data['registered_address_2'] == company.registered_address_2
        assert data['registered_address_town'] == company.registered_address_town
        assert data['registered_address_county'] == company.registered_address_county
        assert data['registered_address_postcode'] == company.registered_address_postcode
        assert (
            data['registered_address_country']['name']
            == company.registered_address_country.name
        )
