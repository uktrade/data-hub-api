from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Advisor, Company
from datahub.core.serializers import NestedRelatedField
from datahub.investment.models import InvestmentProject


class InvestmentProjectSerializer(serializers.ModelSerializer):
    """Serialiser for investment project endpoints."""
    investment_type = NestedRelatedField(meta_models.InvestmentType)
    phase = NestedRelatedField(meta_models.InvestmentProjectPhase)
    investor_company = NestedRelatedField(Company, required=False, allow_null=True)
    intermediate_company = NestedRelatedField(Company, required=False, allow_null=True)
    investment_recipient_company = NestedRelatedField(Company, required=False, allow_null=True)
    # client_contacts TODO

    client_relationship_manager = NestedRelatedField(
        Advisor, required=False, allow_null=True, extra_fields=('first_name', 'last_name')
    )
    referral_source_advisor = NestedRelatedField(
        Advisor, required=False, allow_null=True, extra_fields=('first_name', 'last_name')
    )
    referral_source_activity = NestedRelatedField(meta_models.ReferralSourceActivity,
                                                  required=False, allow_null=True)
    referral_source_activity_website = NestedRelatedField(meta_models.ReferralSourceWebsite,
                                                          required=False, allow_null=True)
    referral_source_activity_marketing = NestedRelatedField(meta_models.ReferralSourceMarketing,
                                                            required=False, allow_null=True)
    referral_source_activity_event = NestedRelatedField(meta_models.Event, required=False,
                                                        allow_null=True)
    fdi_type = NestedRelatedField(meta_models.FDIType, required=False, allow_null=True)
    non_fdi_type = NestedRelatedField(meta_models.NonFDIType, required=False, allow_null=True)
    sector = NestedRelatedField(meta_models.Sector, required=False, allow_null=True)

    # business_activity TODO

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'id', 'name', 'project_code', 'description', 'document_link', 'nda_signed',
            'estimated_land_date', 'project_shareable', 'anonymous_description',
            'not_shareable_reason', 'investment_type', 'phase', 'investor_company',
            'intermediate_company', 'investment_recipient_company',
            'client_relationship_manager', 'referral_source_advisor',
            'referral_source_activity', 'referral_source_activity_website',
            'referral_source_activity_marketing',
            'referral_source_activity_event', 'fdi_type', 'non_fdi_type', 'sector'
        )


class InvestmentProjectValueSerializer(serializers.ModelSerializer):
    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'total_investment', 'foreign_equity_investment', 'government_assistance',
            'number_new_jobs', 'number_safeguarded_jobs', 'r_and_d_budget',
            'non_fdi_r_and_d_budget', 'new_tech_to_uk', 'export_revenue'
        )
