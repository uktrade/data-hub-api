import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.core.utils import model_to_dictionary

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_model_to_dictionary():
    """Model to dictionary without excluded fields and expanded foreign keys."""
    model_instance = CompanyFactory()

    expected_keys = {
        'registered_address_4',
        'trading_address_county',
        'account_manager',
        'trading_address_country',
        'trading_address_4',
        'registered_address_2',
        'alias',
        'archived_by',
        'trading_address_1',
        'description',
        'modified_on',
        'trading_address_2',
        'registered_address_1',
        'archived_on',
        'archived',
        'registered_address_town',
        'trading_address_postcode',
        'registered_address_country',
        'uk_region',
        'created_on',
        'employee_range',
        'registered_address_3',
        'registered_address_postcode',
        'name',
        'website',
        'trading_address_3',
        'registered_address_county',
        'lead',
        'id',
        'sector',
        'trading_address_town',
        'company_number',
        'turnover_range',
        'archived_reason',
        'business_type'
    }
    result = model_to_dictionary(model_instance)
    assert set(result.keys()) == expected_keys
    # KF expansion
    assert result['business_type'] == 'Private limited company'


def test_model_to_dictionary_dont_expand_fk():
    """Model to dictionary without excluded fields and not expanded foreign keys."""
    model_instance = CompanyFactory()
    result = model_to_dictionary(model_instance, expand_foreign_keys=False)
    expected_keys = {
        'registered_address_1',
        'registered_address_postcode',
        'trading_address_3',
        'id',
        'account_manager_id',
        'trading_address_4',
        'employee_range_id',
        'registered_address_town',
        'trading_address_county',
        'business_type_id',
        'trading_address_1',
        'registered_address_country_id',
        'uk_region_id',
        'lead',
        'sector_id',
        'registered_address_county',
        'registered_address_3',
        'alias',
        'trading_address_postcode',
        'trading_address_town',
        'description',
        'registered_address_4',
        'archived_by_id',
        'modified_on',
        'name',
        'trading_address_2',
        'turnover_range_id',
        'website',
        'registered_address_2',
        'created_on',
        'archived_reason',
        'trading_address_country_id',
        'archived',
        'archived_on',
        'company_number'
    }

    assert set(result.keys()) == expected_keys
    # KF ID
    assert result['business_type_id'] == '9ed14e94-5d95-e211-a939-e4115bead28a'


def test_model_to_dictionary_exclude_fields():
    """Model to dictionary excluding some fields and expanded foreign keys."""
    model_instance = CompanyFactory()

    expected_keys = {
        'archived_by',
        'trading_address_1',
        'description',
        'modified_on',
        'trading_address_2',
        'registered_address_1',
        'archived_on',
        'archived',
        'registered_address_town',
        'trading_address_postcode',
        'registered_address_country',
        'uk_region',
        'created_on',
        'employee_range',
        'registered_address_3',
        'registered_address_postcode',
        'name',
        'website',
        'trading_address_3',
        'registered_address_county',
        'lead',
        'id',
        'sector',
        'trading_address_town',
        'company_number',
        'turnover_range',
        'archived_reason',
        'business_type'
    }
    excluded_fields = (
        'registered_address_4',
        'trading_address_county',
        'account_manager',
        'trading_address_country',
        'trading_address_4',
        'registered_address_2',
        'alias'
    )
    result = model_to_dictionary(model_instance, excluded_fields=excluded_fields)
    assert set(result.keys()) == expected_keys
