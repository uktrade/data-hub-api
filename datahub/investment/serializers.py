from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Advisor, Company
from datahub.core.serializers import NestedRelatedField
from datahub.investment.models import InvestmentProject


class InvestmentProjectSerializer(serializers.ModelSerializer):
    """Serialiser for investment project endpoints."""
    investment_type = NestedRelatedField(meta_models.InvestmentType)
    phase = NestedRelatedField(meta_models.InvestmentProjectPhase)
    investor_company = NestedRelatedField(Company)
    intermediate_company = NestedRelatedField(Company)
    investment_recipient_company = NestedRelatedField(Company)
    # client_contacts TODO

    client_relationship_manager = NestedRelatedField(Advisor, extra_fields=('first_name',
                                                                            'last_name'))
    referral_source_advisor = NestedRelatedField(Advisor, extra_fields=('first_name',
                                                                        'last_name'))
    referral_source_activity = NestedRelatedField(meta_models.ReferralSourceActivity)
    referral_source_activity_website = NestedRelatedField(meta_models.ReferralSourceWebsite)
    referral_source_activity_marketing = NestedRelatedField(meta_models.ReferralSourceMarketing)
    referral_source_activity_event = NestedRelatedField(meta_models.Event)
    fdi_type = NestedRelatedField(meta_models.FDIType)
    non_fdi_type = NestedRelatedField(meta_models.NonFDIType)
    sector = NestedRelatedField(meta_models.Sector)
    # business_activity TODO

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = ('id', 'name', 'project_code', 'description', 'document_link', 'nda_signed',
                  'estimated_land_date', 'project_shareable', 'anonymous_description',
                  'not_shareable_reason', 'investment_type', 'phase', 'investor_company',
                  'intermediate_company', 'investment_recipient_company',
                  'client_relationship_manager', 'referral_source_advisor',
                  'referral_source_activity', 'referral_source_activity_website',
                  'referral_source_activity_marketing',
                  'referral_source_activity_event', 'fdi_type', 'non_fdi_type', 'sector')
