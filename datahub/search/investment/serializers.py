from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField
from datahub.investment.models import InvestmentProject
from datahub.search.serializers import (
    SearchSerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchInvestmentProjectSerializer(SearchSerializer):
    """Serialiser used to validate investment project search POST bodies."""

    adviser = SingleOrListField(child=StringUUIDField(), required=False)
    client_relationship_manager = SingleOrListField(child=StringUUIDField(), required=False)
    created_on_after = RelaxedDateTimeField(required=False)
    created_on_before = RelaxedDateTimeField(required=False)
    actual_land_date_after = RelaxedDateTimeField(required=False)
    actual_land_date_before = RelaxedDateTimeField(required=False)
    estimated_land_date_after = RelaxedDateTimeField(required=False)
    estimated_land_date_before = RelaxedDateTimeField(required=False)
    investment_type = SingleOrListField(child=StringUUIDField(), required=False)
    investor_company = SingleOrListField(child=StringUUIDField(), required=False)
    investor_company_country = SingleOrListField(child=StringUUIDField(), required=False)
    country_investment_originates_from = SingleOrListField(child=StringUUIDField(), required=False)
    sector = SingleOrListField(child=StringUUIDField(), required=False)
    sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    stage = SingleOrListField(child=StringUUIDField(), required=False)
    status = SingleOrListField(child=serializers.CharField(), required=False)
    uk_region_location = SingleOrListField(child=StringUUIDField(), required=False)
    level_of_involvement_simplified = SingleOrListField(
        child=serializers.ChoiceField(choices=InvestmentProject.INVOLVEMENT),
        required=False,
    )

    SORT_BY_FIELDS = (
        'actual_land_date',
        'approved_commitment_to_invest',
        'approved_fdi',
        'approved_good_value',
        'approved_high_value',
        'approved_landed',
        'approved_non_fdi',
        'archived',
        'archived_by.name',
        'average_salary.name',
        'business_activities.name',
        'client_cannot_provide_total_investment',
        'client_contacts.name',
        'client_relationship_manager.name',
        'created_on',
        'estimated_land_date',
        'export_revenue',
        'fdi_type.name',
        'foreign_equity_investment',
        'government_assistance',
        'id',
        'intermediate_company.name',
        'investment_type.name',
        'investor_company.name',
        'modified_on',
        'name',
        'new_tech_to_uk',
        'non_fdi_r_and_d_budget',
        'number_new_jobs',
        'project_assurance_adviser.name',
        'project_code',
        'project_manager.name',
        'r_and_d_budget',
        'referral_source_activity.name',
        'referral_source_activity_event',
        'referral_source_activity_marketing.name',
        'referral_source_activity_website.name',
        'referral_source_adviser.name',
        'sector.name',
        'site_decided',
        'stage.name',
        'total_investment',
        'uk_company.name',
    )
