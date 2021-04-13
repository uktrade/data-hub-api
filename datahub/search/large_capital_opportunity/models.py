from elasticsearch_dsl import Boolean, Date, Keyword, Long, Text

from datahub.search import dict_utils, fields
from datahub.search.models import BaseESModel


def _get_adviser_list(col):
    return [dict_utils.contact_or_adviser_dict(c) for c in col.all()]


def _get_many_to_many_list(col):
    return [dict_utils.id_name_dict(c) for c in col.all()]


def _get_company_list(col):
    return [dict_utils.company_dict(c) for c in col.all()]


def _get_investment_project_list(col):
    return [dict_utils.investment_project_dict(i) for i in col.all()]


class LargeCapitalOpportunity(BaseESModel):
    """Elasticsearch representation of LargeCapitalOpportunity."""

    id = Keyword()

    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    type = fields.id_unindexed_name_field()

    description = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    uk_region_locations = fields.id_unindexed_name_field()

    promoters = fields.company_field()

    required_checks_conducted = fields.id_unindexed_name_field()
    required_checks_conducted_by = fields.contact_or_adviser_field(include_dit_team=True)
    required_checks_conducted_on = Date()

    lead_dit_relationship_manager = fields.contact_or_adviser_field(include_dit_team=True)
    other_dit_contacts = fields.contact_or_adviser_field(include_dit_team=True)

    asset_classes = fields.id_unindexed_name_field()
    opportunity_value_type = fields.id_unindexed_name_field()
    opportunity_value = Long()
    construction_risks = fields.id_unindexed_name_field()

    total_investment_sought = Long()
    current_investment_secured = Long()
    investment_types = fields.id_unindexed_name_field()
    estimated_return_rate = fields.id_unindexed_name_field()
    time_horizons = fields.id_unindexed_name_field()
    investment_projects = fields.id_unindexed_name_field()
    status = fields.id_unindexed_name_field()
    sources_of_funding = fields.id_unindexed_name_field()
    dit_support_provided = Boolean()
    reasons_for_abandonment = fields.id_unindexed_name_field()

    created_by = fields.contact_or_adviser_field(include_dit_team=True)
    created_on = Date()
    modified_on = Date()

    _MAIN_FIELD_MAPPINGS = {
        'type': dict_utils.id_name_dict,
        'status': dict_utils.id_name_dict,
        'created_by': dict_utils.adviser_dict_with_team,
    }

    _DETAIL_FIELD_MAPPINGS = {
        'uk_region_locations': _get_many_to_many_list,
        'promoters': _get_company_list,
        'required_checks_conducted': dict_utils.id_name_dict,
        'required_checks_conducted_by': dict_utils.adviser_dict_with_team,
        'lead_dit_relationship_manager': dict_utils.adviser_dict_with_team,
        'other_dit_contacts': _get_adviser_list,
        'asset_classes': _get_many_to_many_list,
        'opportunity_value_type': dict_utils.id_name_dict,
        'construction_risks': _get_many_to_many_list,
        'investment_projects': _get_investment_project_list,
        'sources_of_funding': _get_many_to_many_list,
        'reasons_for_abandonment': _get_many_to_many_list,
    }

    _REQUIREMENT_FIELD_MAPPINGS = {
        'investment_types': _get_many_to_many_list,
        'estimated_return_rate': dict_utils.id_name_dict,
        'time_horizons': _get_many_to_many_list,
    }

    MAPPINGS = {
        **_MAIN_FIELD_MAPPINGS,
        **_DETAIL_FIELD_MAPPINGS,
        **_REQUIREMENT_FIELD_MAPPINGS,
    }
