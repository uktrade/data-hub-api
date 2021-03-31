from elasticsearch_dsl import Boolean, Date, Double, Integer, Keyword, Long, Object, Text

from datahub.search import dict_utils
from datahub.search import fields
from datahub.search.models import BaseESModel


def _related_investment_project_field():
    """Field for a related investment project."""
    return Object(properties={
        'id': Keyword(),
        'name': fields.NormalizedKeyword(),
        'project_code': fields.NormalizedKeyword(),
    })


class InvestmentProject(BaseESModel):
    """Elasticsearch representation of InvestmentProject."""

    id = Keyword()
    actual_land_date = Date()
    actual_uk_regions = fields.id_name_field()
    address_1 = Text()
    address_2 = Text()
    address_town = fields.NormalizedKeyword()
    address_postcode = Text()
    approved_commitment_to_invest = Boolean()
    approved_fdi = Boolean()
    approved_good_value = Boolean()
    approved_high_value = Boolean()
    approved_landed = Boolean()
    approved_non_fdi = Boolean()
    allow_blank_estimated_land_date = Boolean(index=False)
    allow_blank_possible_uk_regions = Boolean(index=False)
    anonymous_description = fields.EnglishText()
    archived = Boolean()
    archived_by = fields.contact_or_adviser_field()
    archived_on = Date()
    archived_reason = Text()
    associated_non_fdi_r_and_d_project = _related_investment_project_field()
    average_salary = fields.id_name_field()
    business_activities = fields.id_name_field()
    client_cannot_provide_foreign_investment = Boolean()
    client_cannot_provide_total_investment = Boolean()
    client_contacts = fields.contact_or_adviser_field()
    client_relationship_manager = fields.contact_or_adviser_field(include_dit_team=True)
    client_requirements = Text(index=False)
    comments = fields.EnglishText()
    country_investment_originates_from = fields.id_name_field()
    country_lost_to = Object(
        properties={
            'id': Keyword(index=False),
            'name': Text(index=False),
        },
    )
    created_on = Date()
    created_by = fields.contact_or_adviser_field(include_dit_team=True)
    date_abandoned = Date()
    date_lost = Date()
    delivery_partners = fields.id_name_field()
    description = fields.EnglishText()
    estimated_land_date = Date()
    export_revenue = Boolean()
    fdi_type = fields.id_name_field()
    fdi_value = fields.id_name_field()
    foreign_equity_investment = Double()
    government_assistance = Boolean()
    incomplete_fields = Text()
    intermediate_company = fields.id_name_field()
    investor_company = fields.id_name_partial_field()
    investor_company_country = fields.id_name_field()
    investment_type = fields.id_name_field()
    investor_type = fields.id_name_field()
    level_of_involvement = fields.id_name_field()
    likelihood_to_land = fields.id_name_field()
    project_assurance_adviser = fields.contact_or_adviser_field(include_dit_team=True)
    project_manager = fields.contact_or_adviser_field(include_dit_team=True)
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    new_tech_to_uk = Boolean()
    non_fdi_r_and_d_budget = Boolean()
    number_new_jobs = Integer()
    number_safeguarded_jobs = Long()
    modified_on = Date()
    project_arrived_in_triage_on = Date()
    project_code = fields.NormalizedKeyword(
        fields={
            'trigram': fields.TrigramText(),
        },
    )
    proposal_deadline = Date()
    other_business_activity = Text(index=False)
    quotable_as_public_case_study = Boolean()
    r_and_d_budget = Boolean()
    reason_abandoned = Text(index=False)
    reason_delayed = Text(index=False)
    reason_lost = Text(index=False)
    referral_source_activity = fields.id_name_field()
    referral_source_activity_event = fields.NormalizedKeyword()
    referral_source_activity_marketing = fields.id_name_field()
    referral_source_activity_website = fields.id_name_field()
    referral_source_adviser = Object(
        properties={
            'id': Keyword(index=False),
            'first_name': Text(index=False),
            'last_name': Text(index=False),
            'name': Text(index=False),
        },
    )
    sector = fields.sector_field()
    site_decided = Boolean()
    some_new_jobs = Boolean()
    specific_programme = fields.id_name_field()
    stage = fields.id_name_field()
    status = fields.NormalizedKeyword()
    team_members = fields.contact_or_adviser_field(include_dit_team=True)
    total_investment = Double()
    uk_company = fields.id_name_partial_field()
    uk_company_decided = Boolean()
    uk_region_locations = fields.id_name_field()
    will_new_jobs_last_two_years = Boolean()
    level_of_involvement_simplified = Keyword()
    latest_interaction = fields.interaction_field()

    gross_value_added = Double()

    MAPPINGS = {
        'actual_uk_regions': lambda col: [
            dict_utils.id_name_dict(c) for c in col.all()
        ],
        'archived_by': dict_utils.contact_or_adviser_dict,
        'associated_non_fdi_r_and_d_project': dict_utils.investment_project_dict,
        'average_salary': dict_utils.id_name_dict,
        'business_activities': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'client_contacts': lambda col: [dict_utils.contact_or_adviser_dict(c) for c in col.all()],
        'client_relationship_manager': dict_utils.adviser_dict_with_team,
        'country_lost_to': dict_utils.id_name_dict,
        'country_investment_originates_from': dict_utils.id_name_dict,
        'created_by': dict_utils.adviser_dict_with_team,
        'delivery_partners': lambda col: [
            dict_utils.id_name_dict(c) for c in col.all()
        ],
        'fdi_type': dict_utils.id_name_dict,
        'fdi_value': dict_utils.id_name_dict,
        'intermediate_company': dict_utils.id_name_dict,
        'investment_type': dict_utils.id_name_dict,
        'investor_company': dict_utils.id_name_dict,
        'investor_company_country': dict_utils.id_name_dict,
        'investor_type': dict_utils.id_name_dict,
        'latest_interaction': dict_utils.interaction_dict,
        'level_of_involvement': dict_utils.id_name_dict,
        'likelihood_to_land': dict_utils.id_name_dict,
        'project_assurance_adviser': dict_utils.adviser_dict_with_team,
        'project_code': str,
        'project_manager': dict_utils.adviser_dict_with_team,
        'referral_source_activity': dict_utils.id_name_dict,
        'referral_source_activity_marketing': dict_utils.id_name_dict,
        'referral_source_activity_website': dict_utils.id_name_dict,
        'referral_source_adviser': dict_utils.contact_or_adviser_dict,
        'sector': dict_utils.sector_dict,
        'specific_programme': dict_utils.id_name_dict,
        'stage': dict_utils.id_name_dict,
        'team_members': lambda col: [
            dict_utils.contact_or_adviser_dict(c.adviser, include_dit_team=True) for c in col.all()
        ],
        'uk_company': dict_utils.id_name_dict,
        'uk_region_locations': lambda col: [
            dict_utils.id_name_dict(c) for c in col.all()
        ],
    }

    SEARCH_FIELDS = (
        'id',
        'name',
        'name.trigram',
        'uk_company.name',
        'uk_company.name.trigram',
        'investor_company.name',
        'investor_company.name.trigram',
        'project_code.trigram',
    )
