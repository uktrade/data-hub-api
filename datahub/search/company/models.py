from operator import attrgetter

from elasticsearch_dsl import Boolean, Completion, Date, Keyword, Text

from datahub.search import dict_utils
from datahub.search import fields
from datahub.search.models import BaseESModel


DOC_TYPE = 'company'


def get_suggestions(db_company):
    """
    A list of fields used by the completion suggester to
    find a record when using an autocomplete search.

    https://www.elastic.co/guide/en/elasticsearch/
    reference/current/search-suggesters-completion.html

    Both the name and trading name of a company are added in full
    and each word within the names are individually added.
    Adding the full names should improve the precision of the search and
    return the company the user is looking for sooner.
    The parts of the names are added so when searching the order
    of the search terms that are entered becomes irrelevant.

    Optional weighting could be added here to boost particular suggestions.
    See above link.
    """
    if db_company.archived:
        return []

    company_name = db_company.name
    alias = db_company.alias or ''

    data = [
        *company_name.split(' '),
        *alias.split(' '),
        company_name,
        alias,
    ]

    return list(filter(None, set(data)))


class Company(BaseESModel):
    """Elasticsearch representation of Company model."""

    id = Keyword()
    archived = Boolean()
    archived_by = fields.nested_contact_or_adviser_field('archived_by')
    archived_on = Date()
    archived_reason = Text()
    business_type = fields.nested_id_name_field()
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
    duns_number = Keyword()
    website = Text()
    suggest = Completion()

    COMPUTED_MAPPINGS = {
        'trading_name': attrgetter('alias'),
        'suggest': get_suggestions,
    }

    MAPPINGS = {
        'archived_by': dict_utils.contact_or_adviser_dict,
        'business_type': dict_utils.id_name_dict,
        'companies_house_data': dict_utils.ch_company_dict,
        'contacts': lambda col: [dict_utils.contact_or_adviser_dict(c) for c in col.all()],
        'employee_range': dict_utils.id_name_dict,
        'export_experience_category': dict_utils.id_name_dict,
        'export_to_countries': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'future_interest_countries': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'global_headquarters': dict_utils.id_name_dict,
        'headquarter_type': dict_utils.id_name_dict,
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
