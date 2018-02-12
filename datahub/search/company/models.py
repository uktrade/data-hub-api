from operator import attrgetter

from django.conf import settings
from elasticsearch_dsl import Boolean, Date, DocType, Keyword, Text

from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class Company(DocType, MapDBModelToDict):
    """Elasticsearch representation of Company model."""

    id = Keyword()
    account_manager = dsl_utils.contact_or_adviser_mapping('account_manager')
    trading_name = dsl_utils.SortableText(
        copy_to=[
            'trading_name_keyword',
            'trading_name_trigram',
        ]
    )
    trading_name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    trading_name_trigram = dsl_utils.TrigramText()
    archived = Boolean()
    archived_by = dsl_utils.contact_or_adviser_mapping('archived_by')
    contacts = dsl_utils.contact_or_adviser_mapping('contacts')
    archived_on = Date()
    archived_reason = Text()
    business_type = dsl_utils.id_name_mapping()
    classification = dsl_utils.id_name_mapping()
    company_number = dsl_utils.SortableCaseInsensitiveKeywordText()
    vat_number = Keyword(index=False)
    companies_house_data = dsl_utils.company_mapping()
    created_on = Date()
    description = dsl_utils.EnglishText()
    employee_range = dsl_utils.id_name_mapping()
    headquarter_type = dsl_utils.id_name_mapping()
    modified_on = Date()
    name = dsl_utils.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()
    one_list_account_owner = dsl_utils.contact_or_adviser_mapping('one_list_account_owner')
    parent = dsl_utils.id_name_mapping()
    global_headquarter = dsl_utils.id_name_mapping()
    reference_code = dsl_utils.SortableCaseInsensitiveKeywordText()
    registered_address_1 = Text()
    registered_address_2 = Text()
    registered_address_country = dsl_utils.id_name_partial_mapping(
        'registered_address_country'
    )
    registered_address_county = Text()
    registered_address_postcode = Text(
        copy_to=[
            'registered_address_postcode_trigram'
        ]
    )
    registered_address_postcode_trigram = dsl_utils.TrigramText()
    registered_address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    sector = dsl_utils.id_name_partial_mapping('sector')
    trading_address_1 = Text()
    trading_address_2 = Text()
    trading_address_country = dsl_utils.id_name_partial_mapping(
        'trading_address_country'
    )
    trading_address_county = Text()
    trading_address_postcode = Text(
        copy_to=['trading_address_postcode_trigram']
    )
    trading_address_postcode_trigram = dsl_utils.TrigramText()
    trading_address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    turnover_range = dsl_utils.id_name_mapping()
    uk_region = dsl_utils.id_name_mapping()
    uk_based = Boolean()
    website = Text()
    export_to_countries = dsl_utils.id_name_mapping()
    future_interest_countries = dsl_utils.id_name_mapping()
    export_experience_category = dsl_utils.id_name_mapping()

    COMPUTED_MAPPINGS = {
        'trading_name': attrgetter('alias')
    }

    MAPPINGS = {
        'companies_house_data': dict_utils.company_dict,
        'account_manager': dict_utils.contact_or_adviser_dict,
        'archived_by': dict_utils.contact_or_adviser_dict,
        'one_list_account_owner': dict_utils.contact_or_adviser_dict,
        'business_type': dict_utils.id_name_dict,
        'classification': dict_utils.id_name_dict,
        'employee_range': dict_utils.id_name_dict,
        'headquarter_type': dict_utils.id_name_dict,
        'parent': dict_utils.id_name_dict,
        'global_headquarter': dict_utils.id_name_dict,
        'registered_address_country': dict_utils.id_name_dict,
        'sector': dict_utils.id_name_dict,
        'trading_address_country': dict_utils.id_name_dict,
        'turnover_range': dict_utils.id_name_dict,
        'uk_region': dict_utils.id_name_dict,
        'address_country': dict_utils.id_name_dict,
        'contacts': lambda col: [dict_utils.contact_or_adviser_dict(c) for c in col.all()],
        'id': str,
        'uk_based': bool,
        'export_to_countries': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'future_interest_countries': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'export_experience_category': dict_utils.id_name_dict,
    }

    IGNORED_FIELDS = (
        'alias',
        'business_leads',
        'children',
        'subsidiaries',
        'created_by',
        'interactions',
        'intermediate_investment_projects',
        'investee_projects',
        'investor_investment_projects',
        'lft',
        'modified_by',
        'orders',
        'rght',
        'tree_id',
        'archived_documents_url_path',
    )

    SEARCH_FIELDS = (
        'name',
        'name_trigram',
        'company_number',
        'trading_name',
        'trading_name_trigram',
        'reference_code',
        'registered_address_country.name_trigram',
        'registered_address_postcode_trigram',
        'sector.name_trigram',
        'trading_address_country.name_trigram',
        'trading_address_postcode_trigram',
        'uk_region.name_trigram'
    )

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'company'
