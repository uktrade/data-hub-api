from functools import partial

from opensearch_dsl import Boolean, Date, Integer, Keyword, Object, Text

from datahub.company.models import CompanyExportCountry
from datahub.search import dict_utils, fields
from datahub.search.models import BaseSearchModel


def _adviser_field_with_indexed_id():
    return Object(
        properties={
            'id': Keyword(),
            'first_name': Text(index=False),
            'last_name': Text(index=False),
            'name': Text(index=False),
        },
    )


class Company(BaseSearchModel):
    """
    OpenSearch representation of Company model.
    """

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
    has_name = Boolean()
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
    adviser = _adviser_field_with_indexed_id()
    trading_names = fields.TextWithTrigram()
    turnover_range = fields.id_name_field()
    uk_region = fields.id_name_field()
    uk_based = Boolean()
    uk_address_postcode = fields.PostcodeKeyword()
    uk_registered_address_postcode = fields.PostcodeKeyword()
    vat_number = Keyword(index=False)
    duns_number = Keyword()
    website = Text()
    latest_interaction_date = Date()
    export_segment = Text()
    export_sub_segment = Text()
    one_list_tier = fields.id_name_field()
    number_of_employees = Integer()
    global_ultimate_duns_number = Keyword()
    is_global_ultimate = Boolean()

    COMPUTED_MAPPINGS = {
        'address': partial(dict_utils.address_dict, prefix='address'),
        'registered_address': partial(dict_utils.address_dict, prefix='registered_address'),
        'one_list_group_global_account_manager': dict_utils.computed_field_function(
            'get_one_list_group_global_account_manager',
            dict_utils.contact_or_adviser_dict,
        ),
        'adviser': dict_utils.computed_field_function(
            'get_one_list_group_core_team',
            dict_utils.core_team_advisers_list_of_dicts,
        ),
        'export_to_countries': lambda obj: [
            dict_utils.id_name_dict(o.country)
            for o in obj.export_countries.all()
            if o.status == CompanyExportCountry.Status.CURRENTLY_EXPORTING
        ],
        'future_interest_countries': lambda obj: [
            dict_utils.id_name_dict(o.country)
            for o in obj.export_countries.all()
            if o.status == CompanyExportCountry.Status.FUTURE_INTEREST
        ],
        'latest_interaction_date': lambda obj: obj.latest_interaction_date,
        'uk_address_postcode': lambda obj: obj.address_postcode if obj.uk_based else '',
        'uk_registered_address_postcode': lambda obj: obj.registered_address_postcode
        if obj.uk_based
        else '',
        'export_segment': lambda obj: obj.export_segment,
        'export_sub_segment': lambda obj: obj.export_sub_segment,
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
        'one_list_tier': dict_utils.id_name_dict,
        'global_ultimate_duns_number': dict_utils.empty_string_to_null,
        'is_global_ultimate': bool,
    }

    SEARCH_FIELDS = (
        'id',
        'name',  # to find 2-letter words
        'name.trigram',
        'company_number',
        'trading_names',  # to find 2-letter words
        'trading_names.trigram',
        'reference_code',
        'sector.name',
        'address.line_1.trigram',
        'address.line_2.trigram',
        'address.town.trigram',
        'address.county.trigram',
        'address.area.name.trigram',
        'address.postcode',
        'address.country.name.trigram',
        'registered_address.line_1.trigram',
        'registered_address.line_2.trigram',
        'registered_address.town.trigram',
        'registered_address.county.trigram',
        'registered_address.area.name.trigram',
        'registered_address.postcode',
        'registered_address.country.name.trigram',
        'export_segment',
        'export_sub_segment',
    )
