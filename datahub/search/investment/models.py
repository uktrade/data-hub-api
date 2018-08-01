from elasticsearch_dsl import Boolean, Date, Double, Integer, Keyword, Long, Text

from .. import dict_utils
from .. import dsl_utils
from ..models import BaseESModel


def _referral_source_adviser_mapping():
    """
    Mapping for referral_source_adviser.

    referral_source_adviser is not using contact_or_adviser_mapping because the mapping for it
    was not explicitly defined, and so was implicitly auto-created.

    The mapping here reflects how it has been auto-created. Further down the line, this mapping
    and contact_or_adviser_mapping will be harmonised.
    """
    return dsl_utils.object_field('id', 'first_name', 'last_name', 'name')


def _country_lost_to_mapping():
    """
    Mapping for country_lost_to.

    The mapping for country_lost_to was implicitly auto-created. This reflects how it was
    auto-created so that we can explicitly define it in the model.
    """
    return dsl_utils.object_field('id', 'name')


class InvestmentProject(BaseESModel):
    """Elasticsearch representation of InvestmentProject."""

    id = Keyword()
    actual_land_date = Date()
    actual_uk_regions = dsl_utils.nested_id_name_field()
    address_1 = Text()
    address_2 = Text()
    address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_postcode = Text()
    approved_commitment_to_invest = Boolean()
    approved_fdi = Boolean()
    approved_good_value = Boolean()
    approved_high_value = Boolean()
    approved_landed = Boolean()
    approved_non_fdi = Boolean()
    allow_blank_estimated_land_date = Boolean(index=False)
    allow_blank_possible_uk_regions = Boolean(index=False)
    anonymous_description = dsl_utils.EnglishText()
    archived = Boolean()
    archived_by = dsl_utils.nested_contact_or_adviser_field('archived_by')
    archived_on = Date()
    archived_reason = Text()
    associated_non_fdi_r_and_d_project = dsl_utils.nested_investment_project_field()
    average_salary = dsl_utils.nested_id_name_field()
    business_activities = dsl_utils.nested_id_name_field()
    client_cannot_provide_foreign_investment = Boolean()
    client_cannot_provide_total_investment = Boolean()
    client_contacts = dsl_utils.nested_contact_or_adviser_field('client_contacts')
    client_relationship_manager = dsl_utils.nested_contact_or_adviser_field(
        'client_relationship_manager', include_dit_team=True
    )
    client_requirements = dsl_utils.TextWithKeyword()
    comments = dsl_utils.EnglishText()
    country_lost_to = _country_lost_to_mapping()
    created_on = Date()
    created_by = dsl_utils.nested_contact_or_adviser_field(
        'created_by', include_dit_team=True
    )
    date_abandoned = Date()
    date_lost = Date()
    delivery_partners = dsl_utils.nested_id_name_field()
    description = dsl_utils.EnglishText()
    estimated_land_date = Date()
    export_revenue = Boolean()
    fdi_type = dsl_utils.nested_id_name_field()
    fdi_value = dsl_utils.nested_id_name_field()
    foreign_equity_investment = Double()
    government_assistance = Boolean()
    intermediate_company = dsl_utils.nested_id_name_field()
    investor_company = dsl_utils.nested_id_name_partial_field('investor_company')
    investor_company_country = dsl_utils.nested_id_name_field()
    investment_type = dsl_utils.nested_id_name_field()
    investor_type = dsl_utils.nested_id_name_field()
    level_of_involvement = dsl_utils.nested_id_name_field()
    likelihood_of_landing = Long()
    project_assurance_adviser = dsl_utils.nested_contact_or_adviser_field(
        'project_assurance_adviser', include_dit_team=True
    )
    project_manager = dsl_utils.nested_contact_or_adviser_field(
        'project_manager', include_dit_team=True
    )
    name = dsl_utils.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()
    new_tech_to_uk = Boolean()
    non_fdi_r_and_d_budget = Boolean()
    number_new_jobs = Integer()
    number_safeguarded_jobs = Long()
    modified_on = Date()
    project_arrived_in_triage_on = Date()
    project_code = dsl_utils.SortableCaseInsensitiveKeywordText(copy_to='project_code_trigram')
    project_code_trigram = dsl_utils.TrigramText()
    proposal_deadline = Date()
    other_business_activity = dsl_utils.TextWithKeyword()
    quotable_as_public_case_study = Boolean()
    r_and_d_budget = Boolean()
    reason_abandoned = dsl_utils.TextWithKeyword()
    reason_delayed = dsl_utils.TextWithKeyword()
    reason_lost = dsl_utils.TextWithKeyword()
    referral_source_activity = dsl_utils.nested_id_name_field()
    referral_source_activity_event = dsl_utils.SortableCaseInsensitiveKeywordText()
    referral_source_activity_marketing = dsl_utils.nested_id_name_field()
    referral_source_activity_website = dsl_utils.nested_id_name_field()
    referral_source_adviser = _referral_source_adviser_mapping()
    sector = dsl_utils.nested_sector_field()
    site_decided = Boolean()
    some_new_jobs = Boolean()
    specific_programme = dsl_utils.nested_id_name_field()
    stage = dsl_utils.nested_id_name_field()
    status = dsl_utils.SortableCaseInsensitiveKeywordText()
    team_members = dsl_utils.nested_contact_or_adviser_field('team_members', include_dit_team=True)
    total_investment = Double()
    uk_company = dsl_utils.nested_id_name_partial_field('uk_company')
    uk_company_decided = Boolean()
    uk_region_locations = dsl_utils.nested_id_name_field()
    will_new_jobs_last_two_years = Boolean()

    MAPPINGS = {
        'id': str,
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
        'created_by': dict_utils.adviser_dict_with_team,
        'delivery_partners': lambda col: [
            dict_utils.id_name_dict(c) for c in col.all()
        ],
        'fdi_type': dict_utils.id_name_dict,
        'fdi_value': dict_utils.id_name_dict,
        'intermediate_company': dict_utils.id_name_dict,
        'investment_type': dict_utils.id_name_dict,
        'investor_company': dict_utils.id_name_dict,
        'investor_type': dict_utils.id_name_dict,
        'level_of_involvement': dict_utils.id_name_dict,
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

    COMPUTED_MAPPINGS = {
        'investor_company_country': dict_utils.computed_nested_id_name_dict(
            'investor_company.registered_address_country'
        ),
    }

    SEARCH_FIELDS = (
        'name',
        'name_trigram',
        'uk_company.name',
        'uk_company.name_trigram',
        'investor_company.name',
        'investor_company.name_trigram',
        'project_code_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = 'investment_project'
