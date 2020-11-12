from elasticsearch_dsl import Date, Keyword, Long

from datahub.search import dict_utils
from datahub.search import fields
from datahub.search.models import BaseESModel


def _get_adviser_list(col):
    return [dict_utils.contact_or_adviser_dict(c['adviser']) for c in col]


def _get_many_to_many_list(col):
    return [dict_utils.id_name_dict(c) for c in col.all()]


class LargeInvestorProfile(BaseESModel):
    """Elasticsearch representation of LargeInvestorProfile."""

    id = Keyword()

    investor_company = fields.company_field()
    country_of_origin = fields.country_field()
    asset_classes_of_interest = fields.id_unindexed_name_field()
    created_by = fields.contact_or_adviser_field(include_dit_team=True)

    investor_type = fields.id_unindexed_name_field()
    global_assets_under_management = Long()
    investable_capital = Long()
    required_checks_conducted = fields.id_unindexed_name_field()

    deal_ticket_sizes = fields.id_unindexed_name_field()
    investment_types = fields.id_unindexed_name_field()
    minimum_return_rate = fields.id_unindexed_name_field()
    time_horizons = fields.id_unindexed_name_field()
    restrictions = fields.id_unindexed_name_field()
    construction_risks = fields.id_unindexed_name_field()
    minimum_equity_percentage = fields.id_unindexed_name_field()
    desired_deal_roles = fields.id_unindexed_name_field()

    uk_region_locations = fields.id_unindexed_name_field()
    other_countries_being_considered = fields.country_field()

    investor_description = fields.EnglishText()
    notes_on_locations = fields.EnglishText()

    created_on = Date()
    modified_on = Date()

    _MAIN_FIELD_MAPPINGS = {
        'asset_classes_of_interest': _get_many_to_many_list,
        'country_of_origin': dict_utils.id_name_dict,
        'investor_company': dict_utils.company_dict,
        'created_by': dict_utils.adviser_dict_with_team,
    }

    _DETAIL_FIELD_MAPPINGS = {
        'investor_type': dict_utils.id_name_dict,
        'required_checks_conducted': dict_utils.id_name_dict,
    }

    _REQUIREMENT_FIELD_MAPPINGS = {
        'deal_ticket_sizes': _get_many_to_many_list,
        'investment_types': _get_many_to_many_list,
        'minimum_return_rate': dict_utils.id_name_dict,
        'time_horizons': _get_many_to_many_list,
        'restrictions': _get_many_to_many_list,
        'construction_risks': _get_many_to_many_list,
        'minimum_equity_percentage': dict_utils.id_name_dict,
        'desired_deal_roles': _get_many_to_many_list,
    }

    _LOCATION_FIELD_MAPPINGS = {
        'uk_region_locations': _get_many_to_many_list,
        'other_countries_being_considered': _get_many_to_many_list,
    }

    MAPPINGS = {
        **_MAIN_FIELD_MAPPINGS,
        **_DETAIL_FIELD_MAPPINGS,
        **_REQUIREMENT_FIELD_MAPPINGS,
        **_LOCATION_FIELD_MAPPINGS,
    }
