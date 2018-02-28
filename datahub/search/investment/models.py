from elasticsearch_dsl import Boolean, Date, DocType, Double, Integer, Keyword, Text

from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class InvestmentProject(DocType, MapDBModelToDict):
    """Elasticsearch representation of InvestmentProject."""

    id = Keyword()
    allow_blank_estimated_land_date = Boolean(index=False)
    allow_blank_possible_uk_regions = Boolean(index=False)
    approved_commitment_to_invest = Boolean()
    approved_fdi = Boolean()
    approved_good_value = Boolean()
    approved_high_value = Boolean()
    approved_landed = Boolean()
    approved_non_fdi = Boolean()
    actual_land_date = Date()
    actual_land_date_documents = dsl_utils.id_uri_mapping()
    business_activities = dsl_utils.id_name_mapping()
    client_contacts = dsl_utils.contact_or_adviser_mapping('client_contacts')
    client_relationship_manager = dsl_utils.contact_or_adviser_mapping(
        'client_relationship_manager', include_dit_team=True
    )
    project_manager = dsl_utils.contact_or_adviser_mapping(
        'project_manager', include_dit_team=True
    )
    project_assurance_adviser = dsl_utils.contact_or_adviser_mapping(
        'project_assurance_adviser', include_dit_team=True
    )
    team_members = dsl_utils.contact_or_adviser_mapping('team_members', include_dit_team=True)
    archived = Boolean()
    archived_reason = Text()
    archived_by = dsl_utils.contact_or_adviser_mapping('archived_by')
    created_on = Date()
    created_by = dsl_utils.contact_or_adviser_mapping(
        'created_by', include_dit_team=True
    )
    modified_on = Date()
    description = dsl_utils.EnglishText()
    comments = dsl_utils.EnglishText()
    anonymous_description = dsl_utils.EnglishText()
    estimated_land_date = Date()
    fdi_type = dsl_utils.id_name_mapping()
    fdi_type_documents = dsl_utils.id_uri_mapping()
    fdi_value = dsl_utils.id_name_mapping()
    intermediate_company = dsl_utils.id_name_mapping()
    uk_company = dsl_utils.id_name_partial_mapping('uk_company')
    investor_company = dsl_utils.id_name_partial_mapping('investor_company')
    investor_company_country = dsl_utils.id_name_mapping()
    investment_type = dsl_utils.id_name_mapping()
    investor_type = dsl_utils.id_name_mapping()
    level_of_involvement = dsl_utils.id_name_mapping()
    specific_programme = dsl_utils.id_name_mapping()
    name = dsl_utils.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()
    r_and_d_budget = Boolean()
    non_fdi_r_and_d_budget = Boolean()
    associated_non_fdi_r_and_d_project = dsl_utils.investment_project_mapping()
    new_tech_to_uk = Boolean()
    export_revenue = Boolean()
    uk_region_locations = dsl_utils.id_name_mapping()
    actual_uk_regions = dsl_utils.id_name_mapping()
    delivery_partners = dsl_utils.id_name_mapping()
    site_decided = Boolean()
    government_assistance = Boolean()
    client_cannot_provide_total_investment = Boolean()
    total_investment = Double()
    foreign_equity_investment = Double()
    number_new_jobs = Integer()
    operations_commenced_documents = dsl_utils.id_uri_mapping()
    stage = dsl_utils.id_name_mapping()
    project_code = dsl_utils.SortableCaseInsensitiveKeywordText(copy_to='project_code_trigram')
    project_code_trigram = dsl_utils.TrigramText()
    referral_source_activity = dsl_utils.id_name_mapping()
    referral_source_activity_marketing = dsl_utils.id_name_mapping()
    referral_source_activity_website = dsl_utils.id_name_mapping()
    referral_source_activity_event = dsl_utils.SortableCaseInsensitiveKeywordText()
    referral_source_advisor = dsl_utils.contact_or_adviser_mapping('referral_source_advisor')
    sector = dsl_utils.id_name_partial_mapping('sector')
    status = dsl_utils.SortableCaseInsensitiveKeywordText()
    average_salary = dsl_utils.id_name_mapping()
    date_lost = Date()
    date_abandoned = Date()

    MAPPINGS = {
        'id': str,
        'actual_land_date_documents': lambda col: [dict_utils.id_uri_dict(c) for c in col.all()],
        'business_activities': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'client_contacts': lambda col: [dict_utils.contact_or_adviser_dict(c) for c in col.all()],
        'client_relationship_manager': dict_utils.adviser_dict_with_team,
        'delivery_partners': lambda col: [
            dict_utils.id_name_dict(c) for c in col.all()
        ],
        'team_members': lambda col: [
            dict_utils.contact_or_adviser_dict(c.adviser, include_dit_team=True) for c in col.all()
        ],
        'fdi_type': dict_utils.id_name_dict,
        'fdi_type_documents': lambda col: [dict_utils.id_uri_dict(c) for c in col.all()],
        'fdi_value': dict_utils.id_name_dict,
        'intermediate_company': dict_utils.id_name_dict,
        'investor_company': dict_utils.id_name_dict,
        'investor_type': dict_utils.id_name_dict,
        'level_of_involvement': dict_utils.id_name_dict,
        'specific_programme': dict_utils.id_name_dict,
        'uk_region_locations': lambda col: [
            dict_utils.id_name_dict(c) for c in col.all()
        ],
        'actual_uk_regions': lambda col: [
            dict_utils.id_name_dict(c) for c in col.all()
        ],
        'uk_company': dict_utils.id_name_dict,
        'investment_type': dict_utils.id_name_dict,
        'associated_non_fdi_r_and_d_project': dict_utils.investment_project_dict,
        'operations_commenced_documents': lambda col: [
            dict_utils.id_uri_dict(c) for c in col.all()
        ],
        'stage': dict_utils.id_name_dict,
        'referral_source_activity': dict_utils.id_name_dict,
        'referral_source_activity_marketing': dict_utils.id_name_dict,
        'referral_source_activity_website': dict_utils.id_name_dict,
        'referral_source_adviser': dict_utils.contact_or_adviser_dict,
        'sector': dict_utils.id_name_dict,
        'project_code': str,
        'average_salary': dict_utils.id_name_dict,
        'archived_by': dict_utils.contact_or_adviser_dict,
        'project_manager': dict_utils.adviser_dict_with_team,
        'project_assurance_adviser': dict_utils.adviser_dict_with_team,
        'country_lost_to': dict_utils.id_name_dict,
        'created_by': dict_utils.adviser_dict_with_team,
    }

    COMPUTED_MAPPINGS = {
        'investor_company_country': dict_utils.computed_nested_id_name_dict(
            'investor_company.registered_address_country'
        ),
    }

    IGNORED_FIELDS = (
        'cdms_project_code',
        'client_considering_other_countries',
        'competitor_countries',
        'documents',
        'interactions',
        'investmentprojectcode',
        'modified_by',
        'strategic_drivers',
        'archived_documents_url_path',
    )

    SEARCH_FIELDS = (
        'name',
        'name_trigram',
        'uk_company.name',
        'uk_company.name_trigram',
        'investor_company.name',
        'investor_company.name_trigram',
        'project_code_trigram',
        'sector.name_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = 'investment_project'
