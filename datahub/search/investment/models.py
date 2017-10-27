from django.conf import settings
from elasticsearch_dsl import Boolean, Date, DocType, Double, Integer, Keyword, Text

from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class InvestmentProject(DocType, MapDBModelToDict):
    """Elasticsearch representation of InvestmentProject."""

    id = Keyword()
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
    client_relationship_manager = dsl_utils.id_name_mapping()
    project_manager = dsl_utils.contact_or_adviser_mapping('project_manager')
    project_assurance_adviser = dsl_utils.contact_or_adviser_mapping('project_assurance_adviser')
    team_members = dsl_utils.contact_or_adviser_mapping('team_members')
    archived = Boolean()
    archived_reason = Text()
    archived_by = dsl_utils.contact_or_adviser_mapping('archived_by')
    created_on = Date()
    modified_on = Date()
    description = dsl_utils.EnglishText()
    anonymous_description = dsl_utils.EnglishText()
    estimated_land_date = Date()
    fdi_type = dsl_utils.id_name_mapping()
    fdi_type_documents = dsl_utils.id_uri_mapping()
    fdi_value = dsl_utils.id_name_mapping()
    intermediate_company = dsl_utils.id_name_mapping()
    uk_company = dsl_utils.id_name_mapping()
    investor_company = dsl_utils.id_name_mapping()
    investor_company_country = dsl_utils.id_name_mapping()
    investment_type = dsl_utils.id_name_mapping()
    name = dsl_utils.SortableText()
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()
    r_and_d_budget = Boolean()
    non_fdi_r_and_d_budget = Boolean()
    associated_non_fdi_r_and_d_project = dsl_utils.investment_project_mapping()
    new_tech_to_uk = Boolean()
    export_revenue = Boolean()
    uk_region_locations = dsl_utils.id_name_mapping()
    site_decided = Boolean()
    government_assistance = Boolean()
    client_cannot_provide_total_investment = Boolean()
    total_investment = Double()
    foreign_equity_investment = Double()
    number_new_jobs = Integer()
    non_fdi_type = dsl_utils.id_name_mapping()
    operations_commenced_documents = dsl_utils.id_uri_mapping()
    stage = dsl_utils.id_name_mapping()
    project_code = dsl_utils.SortableCaseInsensitiveKeywordText()
    referral_source_activity = dsl_utils.id_name_mapping()
    referral_source_activity_marketing = dsl_utils.id_name_mapping()
    referral_source_activity_website = dsl_utils.id_name_mapping()
    referral_source_activity_event = dsl_utils.SortableCaseInsensitiveKeywordText()
    referral_source_advisor = dsl_utils.contact_or_adviser_mapping('referral_source_advisor')
    sector = dsl_utils.id_name_mapping()
    average_salary = dsl_utils.id_name_mapping()
    date_lost = Date()
    date_abandoned = Date()

    MAPPINGS = {
        'id': str,
        'actual_land_date_documents': lambda col: [dict_utils.id_uri_dict(c) for c in col.all()],
        'business_activities': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'client_contacts': lambda col: [dict_utils.contact_or_adviser_dict(c) for c in col.all()],
        'client_relationship_manager': dict_utils.id_name_dict,
        'team_members': lambda col: [
            dict_utils.contact_or_adviser_dict(c.adviser) for c in col.all()
        ],
        'fdi_type': dict_utils.id_name_dict,
        'fdi_type_documents': lambda col: [dict_utils.id_uri_dict(c) for c in col.all()],
        'fdi_value': dict_utils.id_name_dict,
        'intermediate_company': dict_utils.id_name_dict,
        'investor_company': dict_utils.id_name_dict,
        'uk_region_locations': lambda col: [
            dict_utils.id_name_dict(c) for c in col.all()
        ],
        'uk_company': dict_utils.id_name_dict,
        'investment_type': dict_utils.id_name_dict,
        'associated_non_fdi_r_and_d_project': dict_utils.investment_project_dict,
        'non_fdi_type': dict_utils.id_name_dict,
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
        'project_manager': dict_utils.contact_or_adviser_dict,
        'project_assurance_adviser': dict_utils.contact_or_adviser_dict,
        'country_lost_to': dict_utils.id_name_dict,
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
        'created_by',
        'documents',
        'interactions',
        'investmentprojectcode',
        'modified_by',
        'strategic_drivers',
    )

    SEARCH_FIELDS = [
        'business_activities.name',
        'intermediate_company.name',
        'investor_company.name',
        'sector.name',
        'uk_company.name',
    ]

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'investment_project'
