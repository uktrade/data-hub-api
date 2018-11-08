from operator import attrgetter

from elasticsearch_dsl import Boolean, Date, Keyword, Text

from datahub.search import dict_utils
from datahub.search import fields
from datahub.search.models import BaseESModel


DOC_TYPE = 'company'


class Company(BaseESModel):
    """Elasticsearch representation of Company model."""

    id = Keyword()
    archived = Boolean()
    archived_by = fields.nested_contact_or_adviser_field('archived_by')
    archived_on = Date()
    archived_reason = Text()
    business_type = fields.nested_id_name_field()
    classification = fields.nested_id_name_field()
    companies_house_data = fields.nested_ch_company_field()
    company_number = fields.SortableCaseInsensitiveKeywordText()
    contacts = fields.nested_contact_or_adviser_field('contacts')
    created_on = Date()
    description = fields.EnglishText()
    employee_range = fields.nested_id_name_field()
    export_experience_category = fields.nested_id_name_field()
    export_to_countries = fields.nested_id_name_field()
    future_interest_countries = fields.nested_id_name_field()
    global_headquarters = fields.nested_id_name_field()
    headquarter_type = fields.nested_id_name_field()
    modified_on = Date()
    name = fields.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = fields.SortableCaseInsensitiveKeywordText()
    name_trigram = fields.TrigramText()
    one_list_account_owner = fields.nested_contact_or_adviser_field('one_list_account_owner')
    reference_code = fields.SortableCaseInsensitiveKeywordText()
    registered_address_1 = Text()
    registered_address_2 = Text()
    registered_address_town = fields.SortableCaseInsensitiveKeywordText()
    registered_address_county = Text()
    registered_address_country = fields.nested_id_name_partial_field(
        'registered_address_country',
    )
    registered_address_postcode = Text(
        copy_to=[
            'registered_address_postcode_trigram',
        ],
    )
    registered_address_postcode_trigram = fields.TrigramText()
    sector = fields.nested_sector_field()
    trading_address_1 = Text()
    trading_address_2 = Text()
    trading_address_town = fields.SortableCaseInsensitiveKeywordText()
    trading_address_county = Text()
    trading_address_postcode = Text(
        copy_to=['trading_address_postcode_trigram'],
    )
    trading_address_postcode_trigram = fields.TrigramText()
    trading_address_country = fields.nested_id_name_partial_field(
        'trading_address_country',
    )
    trading_name = fields.SortableText(
        copy_to=[
            'trading_name_keyword',
            'trading_name_trigram',
        ],
    )
    trading_name_keyword = fields.SortableCaseInsensitiveKeywordText()
    trading_name_trigram = fields.TrigramText()
    turnover_range = fields.nested_id_name_field()
    uk_region = fields.nested_id_name_field()
    uk_based = Boolean()
    vat_number = Keyword(index=False)
    website = Text()

    COMPUTED_MAPPINGS = {
        'trading_name': attrgetter('alias'),
    }

    MAPPINGS = {
        'id': str,
        'archived_by': dict_utils.contact_or_adviser_dict,
        'business_type': dict_utils.id_name_dict,
        'classification': dict_utils.id_name_dict,
        'companies_house_data': dict_utils.ch_company_dict,
        'contacts': lambda col: [dict_utils.contact_or_adviser_dict(c) for c in col.all()],
        'employee_range': dict_utils.id_name_dict,
        'export_experience_category': dict_utils.id_name_dict,
        'export_to_countries': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'future_interest_countries': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'global_headquarters': dict_utils.id_name_dict,
        'headquarter_type': dict_utils.id_name_dict,
        'one_list_account_owner': dict_utils.contact_or_adviser_dict,
        'registered_address_country': dict_utils.id_name_dict,
        'sector': dict_utils.sector_dict,
        'trading_address_country': dict_utils.id_name_dict,
        'turnover_range': dict_utils.id_name_dict,
        'uk_based': bool,
        'uk_region': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = (
        'name',
        'name_trigram',
        'company_number',
        'trading_name',
        'trading_name_trigram',
        'reference_code',
        'registered_address_country.name_trigram',
        'registered_address_postcode_trigram',
        'trading_address_country.name_trigram',
        'trading_address_postcode_trigram',
        'uk_region.name_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
