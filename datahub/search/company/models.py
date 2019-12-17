import itertools
from functools import partial

from elasticsearch_dsl import Boolean, Date, Keyword, Object, Text
from elasticsearch_dsl import Completion

from datahub.company.models import CompanyExportCountry
from datahub.search import dict_utils, fields
from datahub.search.models import BaseESModel
from datahub.search.utils import get_unique_values_and_exclude_nulls_from_list

DOC_TYPE = 'company'


def _adviser_field_with_indexed_id():
    return Object(
        properties={
            'id': Keyword(),
            'first_name': Text(index=False),
            'last_name': Text(index=False),
            'name': Text(index=False),
        },
    )


def _get_country_id_dict(obj):
    if obj is None:
        return

    return {
        'id': str(obj.country_id),
    }


def get_suggestions(db_company):
    """
    Returns a dictionary with the keys input and context.
    input contains a list of fields used by the completion suggester to
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

    contexts contains a dictionary with any supported filters.

    https://www.elastic.co/guide/en/elasticsearch/reference/current/suggester-context.html

    context - country a list of UUIDs of the countries where the company is based.
    """
    if db_company.archived:
        return {}

    names = [
        db_company.name,
        *db_company.trading_names,
    ]

    data = [
        *itertools.chain(
            *[name.split(' ') for name in names],
        ),
        *names,
    ]

    countries = [
        db_company.registered_address_country_id,
        db_company.address_country_id,
    ]

    return {
        'input': get_unique_values_and_exclude_nulls_from_list(data),
        'contexts': {
            'country': get_unique_values_and_exclude_nulls_from_list(countries),
        },
    }


class Company(BaseESModel):
    """Elasticsearch representation of Company model."""

    id = Keyword()
    archived = Boolean()
    archived_by = fields.contact_or_adviser_field()
    archived_on = Date()
    archived_reason = Text()
    business_type = fields.id_name_field()
    company_number = fields.NormalizedKeyword()
    created_on = Date()
    description = fields.EnglishText()
    employee_range = fields.id_name_field()
    export_experience_category = fields.id_name_field()
    export_to_countries = fields.id_name_field()
    future_interest_countries = fields.id_name_field()
    global_headquarters = fields.id_name_field()
    headquarter_type = fields.id_name_field()
    modified_on = Date()
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    reference_code = fields.NormalizedKeyword()
    sector = fields.sector_field()
    address = fields.address_field()
    registered_address = fields.address_field()
    one_list_group_global_account_manager = _adviser_field_with_indexed_id()
    trading_names = fields.TextWithTrigram()
    turnover_range = fields.id_name_field()
    uk_region = fields.id_name_field()
    uk_based = Boolean()
    uk_address_postcode = fields.PostcodeKeyword()
    uk_registered_address_postcode = fields.PostcodeKeyword()
    vat_number = Keyword(index=False)
    duns_number = Keyword()
    website = Text()
    suggest = Completion(
        contexts=[
            {
                'name': 'country',
                'type': 'category',
            },
        ],
    )
    latest_interaction_date = Date()

    COMPUTED_MAPPINGS = {
        'suggest': get_suggestions,
        'address': partial(dict_utils.address_dict, prefix='address'),
        'registered_address': partial(dict_utils.address_dict, prefix='registered_address'),
        'one_list_group_global_account_manager': dict_utils.computed_field_function(
            'get_one_list_group_global_account_manager',
            dict_utils.contact_or_adviser_dict,
        ),
        'export_to_countries': lambda obj: [
            _get_country_id_dict(o) for o in obj.export_countries.all()
            if o.status == CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting
        ],
        'future_interest_countries': lambda obj: [
            _get_country_id_dict(o) for o in obj.export_countries.all()
            if o.status == CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest
        ],
        'latest_interaction_date': lambda obj: obj.latest_interaction_date,
        'uk_address_postcode': lambda obj: obj.address_postcode if obj.uk_based else '',
        'uk_registered_address_postcode':
            lambda obj: obj.registered_address_postcode if obj.uk_based else '',
    }

    MAPPINGS = {
        'archived_by': dict_utils.contact_or_adviser_dict,
        'business_type': dict_utils.id_name_dict,
        'employee_range': dict_utils.id_name_dict,
        'export_experience_category': dict_utils.id_name_dict,
        'global_headquarters': dict_utils.id_name_dict,
        'headquarter_type': dict_utils.id_name_dict,
        'sector': dict_utils.sector_dict,

        'turnover_range': dict_utils.id_name_dict,
        'uk_based': bool,
        'uk_region': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = (
        'id',
        'name',  # to find 2-letter words
        'name.trigram',
        'company_number',
        'trading_names',  # to find 2-letter words
        'trading_names.trigram',
        'reference_code',

        'address.country.name.trigram',
        'address.postcode.trigram',
        'registered_address.country.name.trigram',
        'registered_address.postcode.trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
