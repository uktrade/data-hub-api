from django.conf import settings
from elasticsearch_dsl import Boolean, Date, DocType, String

from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class Company(DocType, MapDBModelToDict):
    """Elasticsearch representation of Company model."""

    id = String(index='not_analyzed')
    account_manager = dsl_utils._contact_mapping('account_manager')
    alias = String()
    archived = Boolean()
    archived_by = dsl_utils._contact_mapping('archived_by')
    contacts = dsl_utils._contact_mapping('contacts')
    archived_on = Date()
    archived_reason = String()
    business_type = dsl_utils._id_name_mapping()
    classification = dsl_utils._id_name_mapping()
    company_number = dsl_utils.CaseInsensitiveKeywordString()
    companies_house_data = dsl_utils._company_mapping()
    created_on = Date()
    description = String()
    employee_range = dsl_utils._id_name_mapping()
    headquarter_type = dsl_utils._id_name_mapping()
    modified_on = Date()
    name = String(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.CaseInsensitiveKeywordString()
    name_trigram = dsl_utils.TrigramString()
    one_list_account_owner = dsl_utils._contact_mapping('one_list_account_owner')
    parent = dsl_utils._id_name_mapping()
    registered_address_1 = String()
    registered_address_2 = String()
    registered_address_country = dsl_utils._id_name_mapping()
    registered_address_county = String()
    registered_address_postcode = String()
    registered_address_town = dsl_utils.CaseInsensitiveKeywordString()
    sector = dsl_utils._id_name_mapping()
    trading_address_1 = String()
    trading_address_2 = String()
    trading_address_country = dsl_utils._id_name_mapping()
    trading_address_county = String()
    trading_address_postcode = String()
    trading_address_town = dsl_utils.CaseInsensitiveKeywordString()
    turnover_range = dsl_utils._id_name_mapping()
    uk_region = dsl_utils._id_name_mapping()
    uk_based = Boolean()
    website = String()
    export_to_countries = dsl_utils._id_name_mapping()
    future_interest_countries = dsl_utils._id_name_mapping()

    MAPPINGS = {
        'companies_house_data': dict_utils._company_dict,
        'account_manager': dict_utils._contact_dict,
        'archived_by': dict_utils._contact_dict,
        'one_list_account_owner': dict_utils._contact_dict,
        'business_type': dict_utils._id_name_dict,
        'classification': dict_utils._id_name_dict,
        'employee_range': dict_utils._id_name_dict,
        'headquarter_type': dict_utils._id_name_dict,
        'parent': dict_utils._id_name_dict,
        'registered_address_country': dict_utils._id_name_dict,
        'sector': dict_utils._id_name_dict,
        'trading_address_country': dict_utils._id_name_dict,
        'turnover_range': dict_utils._id_name_dict,
        'uk_region': dict_utils._id_name_dict,
        'address_country': dict_utils._id_name_dict,
        'contacts': lambda col: [dict_utils._contact_dict(c) for c in col.all()],
        'id': str,
        'uk_based': bool,
        'export_to_countries': lambda col: [dict_utils._id_name_dict(c) for c in col.all()],
        'future_interest_countries': lambda col: [dict_utils._id_name_dict(c) for c in col.all()],
    }

    IGNORED_FIELDS = (
        'business_leads',
        'children',
        'created_by',
        'interactions',
        'intermediate_investment_projects',
        'investee_projects',
        'investor_investment_projects',
        'lft',
        'modified_by',
        'orders',
        'rght',
        'servicedeliverys',
        'tree_id'
    )

    SEARCH_FIELDS = [
        'classification.name',
        'export_to_countries.name',
        'future_interest_countries.name',
        'registered_address_country.name',
        'registered_address_town',
        'sector.name',
        'trading_address_country.name',
        'trading_address_town',
        'uk_region.name',
        'website'
    ]

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'company'
