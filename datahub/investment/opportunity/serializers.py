from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Advisor, Company
from datahub.core.serializers import NestedRelatedField
from datahub.investment.investor_profile.models import (
    AssetClassInterest,
    ConstructionRisk,
    LargeCapitalInvestmentType,
    ReturnRate,
    TimeHorizon,
)
from datahub.investment.investor_profile.serializers import RequiredChecksConductedSerializer
from datahub.investment.investor_profile.validate import get_incomplete_fields
from datahub.investment.opportunity.models import (
    AbandonmentReason,
    LargeCapitalOpportunity,
    OpportunityStatus,
    OpportunityType,
    OpportunityValueType,
    SourceOfFunding,
)
from datahub.investment.project.models import InvestmentProject

BASE_FIELDS = [
    'id',
    'created_on',
    'modified_on',
    'type',
    'status',
    'name',
    'description',
    'dit_support_provided',
]

INCOMPLETE_LIST_FIELDS = [
    'incomplete_details_fields',
    'incomplete_requirements_fields',
    'incomplete_location_fields',
]


LARGE_CAPITAL_DETAILS_FIELDS = [
    'opportunity_value_type',
    'opportunity_value',
    'required_checks_conducted',
    'investment_projects',
    'reasons_for_abandonment',
    'promoters',
    'lead_dit_relationship_manager',
    'other_dit_contacts',
    'total_investment_sought',
    'current_investment_secured',
]

LARGE_CAPITAL_ADDITIONAL_DETAILS_FIELDS = [
    'required_checks_conducted_on',
    'required_checks_conducted_by',
]


LARGE_CAPITAL_REQUIREMENTS_FIELDS = [
    'investment_types',
    'estimated_return_rate',
    'time_horizons',
    'construction_risks',
    'sources_of_funding',
    'asset_classes',
]


LARGE_CAPITAL_LOCATION_FIELDS = [
    'uk_region_locations',
]

ALL_LARGE_CAPITAL_OPPORTUNITY_FIELDS = [
    *BASE_FIELDS,
    *INCOMPLETE_LIST_FIELDS,
    *LARGE_CAPITAL_DETAILS_FIELDS,
    *LARGE_CAPITAL_ADDITIONAL_DETAILS_FIELDS,
    *LARGE_CAPITAL_REQUIREMENTS_FIELDS,
    *LARGE_CAPITAL_LOCATION_FIELDS,
]


class LargeCapitalOpportunitySerializer(RequiredChecksConductedSerializer):
    """Large capital opportunity serializer."""

    type = NestedRelatedField(
        OpportunityType,
        allow_null=False,
    )
    status = NestedRelatedField(
        OpportunityStatus,
        allow_null=False,
    )

    created_on = serializers.DateTimeField(
        read_only=True,
    )

    modified_on = serializers.DateTimeField(
        read_only=True,
    )

    uk_region_locations = NestedRelatedField(
        meta_models.UKRegion,
        many=True,
        required=False,
    )
    promoters = NestedRelatedField(
        Company,
        many=True,
        required=False,
    )

    lead_dit_relationship_manager = NestedRelatedField(
        Advisor,
        required=False,
        allow_null=True,
    )
    other_dit_contacts = NestedRelatedField(
        Advisor,
        many=True,
        required=False,
        allow_null=True,
    )

    asset_classes = NestedRelatedField(
        AssetClassInterest,
        many=True,
        required=False,
    )

    opportunity_value = serializers.DecimalField(max_digits=19, decimal_places=0, required=False)

    opportunity_value_type = NestedRelatedField(
        OpportunityValueType,
        required=False,
    )

    construction_risks = NestedRelatedField(
        ConstructionRisk,
        many=True,
        required=False,
    )

    investment_types = NestedRelatedField(
        LargeCapitalInvestmentType,
        many=True,
        required=False,
    )

    estimated_return_rate = NestedRelatedField(
        ReturnRate,
        required=False,
        allow_null=True,
    )

    time_horizons = NestedRelatedField(
        TimeHorizon,
        many=True,
        required=False,
    )

    investment_projects = NestedRelatedField(
        InvestmentProject,
        many=True,
        required=False,
    )

    sources_of_funding = NestedRelatedField(
        SourceOfFunding,
        many=True,
        required=False,
    )

    reasons_for_abandonment = NestedRelatedField(
        AbandonmentReason,
        many=True,
        required=False,
    )

    incomplete_details_fields = serializers.SerializerMethodField()

    incomplete_requirements_fields = serializers.SerializerMethodField()

    incomplete_location_fields = serializers.SerializerMethodField()

    def get_incomplete_details_fields(self, instance):
        """Returns a list of all the detail fields that are incomplete."""
        return get_incomplete_fields(
            instance,
            LARGE_CAPITAL_DETAILS_FIELDS,
            LargeCapitalOpportunity,
        )

    def get_incomplete_requirements_fields(self, instance):
        """Returns a list of all the requirement fields that are incomplete."""
        return get_incomplete_fields(
            instance,
            LARGE_CAPITAL_REQUIREMENTS_FIELDS,
            LargeCapitalOpportunity,
        )

    def get_incomplete_location_fields(self, instance):
        """Returns a list of all the location fields that are incomplete."""
        return get_incomplete_fields(
            instance,
            LARGE_CAPITAL_LOCATION_FIELDS,
            LargeCapitalOpportunity,
        )

    class Meta(RequiredChecksConductedSerializer.Meta):
        model = LargeCapitalOpportunity
        fields = ALL_LARGE_CAPITAL_OPPORTUNITY_FIELDS
