from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Company
from datahub.core.serializers import ConstantModelSerializer, NestedRelatedField
from datahub.investment.investor_profile.constants import ProfileType as ProfileTypeConstant
from datahub.investment.investor_profile.models import (
    AssetClassInterest,
    AssetClassInterestSector,
    ConstructionRisk,
    DealTicketSize,
    DesiredDealRole,
    EquityPercentage,
    InvestorProfile,
    InvestorType,
    LargeCapitalInvestmentType,
    RequiredChecksConducted,
    Restriction,
    ReturnRate,
    TimeHorizon,
)
from datahub.investment.investor_profile.validate import get_incomplete_fields


BASE_FIELDS = [
    'id',
    'created_on',
    'modified_on',
    'investor_company',
]

INCOMPLETE_LIST_FIELDS = [
    'incomplete_details_fields',
    'incomplete_requirements_fields',
    'incomplete_location_fields',
]


LARGE_CAPITAL_DETAILS_FIELDS = [
    'investor_type',
    'investable_capital',
    'global_assets_under_management',
    'investor_description',
    'required_checks_conducted',
]


LARGE_CAPITAL_REQUIREMENTS_FIELDS = [
    'deal_ticket_sizes',
    'investment_types',
    'minimum_return_rate',
    'time_horizons',
    'construction_risks',
    'minimum_equity_percentage',
    'desired_deal_roles',
    'restrictions',
    'asset_classes_of_interest',
]


LARGE_CAPITAL_LOCATION_FIELDS = [
    'uk_region_locations',
    'notes_on_locations',
    'other_countries_being_considered',
]

ALL_LARGE_CAPITAL_FIELDS = (
    BASE_FIELDS
    + INCOMPLETE_LIST_FIELDS
    + LARGE_CAPITAL_DETAILS_FIELDS
    + LARGE_CAPITAL_REQUIREMENTS_FIELDS
    + LARGE_CAPITAL_LOCATION_FIELDS
)


class LargeCapitalInvestorProfileSerializer(serializers.ModelSerializer):
    """Large capital investor profile serializer."""

    investor_company = NestedRelatedField(
        Company,
        allow_null=False,
    )

    created_on = serializers.DateTimeField(
        read_only=True,
    )

    modified_on = serializers.DateTimeField(
        read_only=True,
    )

    investor_type = NestedRelatedField(
        InvestorType,
        required=False,
    )

    required_checks_conducted = NestedRelatedField(
        RequiredChecksConducted,
        required=False,
    )

    deal_ticket_sizes = NestedRelatedField(
        DealTicketSize,
        many=True,
        required=False,
    )

    investment_types = NestedRelatedField(
        LargeCapitalInvestmentType,
        many=True,
        required=False,
    )

    minimum_return_rate = NestedRelatedField(
        ReturnRate,
        required=False,
    )

    time_horizons = NestedRelatedField(
        TimeHorizon,
        many=True,
        required=False,
    )

    restrictions = NestedRelatedField(
        Restriction,
        many=True,
        required=False,
    )

    construction_risks = NestedRelatedField(
        ConstructionRisk,
        many=True,
        required=False,
    )

    minimum_equity_percentage = NestedRelatedField(
        EquityPercentage,
        required=False,
    )

    desired_deal_roles = NestedRelatedField(
        DesiredDealRole,
        many=True,
        required=False,
    )

    uk_region_locations = NestedRelatedField(
        meta_models.UKRegion,
        many=True,
        required=False,
    )

    other_countries_being_considered = NestedRelatedField(
        meta_models.Country,
        many=True,
        required=False,
    )

    asset_classes_of_interest = NestedRelatedField(
        AssetClassInterest,
        many=True,
        required=False,
    )

    incomplete_details_fields = serializers.SerializerMethodField()

    incomplete_requirements_fields = serializers.SerializerMethodField()

    incomplete_location_fields = serializers.SerializerMethodField()

    def get_incomplete_details_fields(self, instance):
        """Returns a list of all the detail fields that are incomplete."""
        return get_incomplete_fields(instance, LARGE_CAPITAL_DETAILS_FIELDS)

    def get_incomplete_requirements_fields(self, instance):
        """Returns a list of all the requirement fields that are incomplete."""
        return get_incomplete_fields(instance, LARGE_CAPITAL_REQUIREMENTS_FIELDS)

    def get_incomplete_location_fields(self, instance):
        """Returns a list of all the location fields that are incomplete."""
        return get_incomplete_fields(instance, LARGE_CAPITAL_LOCATION_FIELDS)

    def validate_investor_company(self, value):
        """
        Validates that the company has not changed and that the company does not already
        have a large capital investment profile.
        """
        if self.instance and self.instance.investor_company_id != value.id:
            raise serializers.ValidationError(
                'Investor company can not be updated',
            )

        profile_id = getattr(self.instance, 'id', None)
        if value.investor_profiles.filter(
            profile_type_id=ProfileTypeConstant.large.value.id,
        ).exclude(
            id=profile_id,
        ).exists():
            raise serializers.ValidationError(
                'Investor company already has large capital investor profile',
            )
        return value

    def create(self, validated_data):
        """Overrides the create method to add the large profile type id into the data."""
        validated_data['profile_type_id'] = ProfileTypeConstant.large.value.id
        return super().create(validated_data)

    class Meta:
        model = InvestorProfile
        fields = ALL_LARGE_CAPITAL_FIELDS


class AssetClassInterestSerializer(ConstantModelSerializer):
    """Asset class interest serializer."""

    asset_class_interest_sector = NestedRelatedField(
        AssetClassInterestSector,
        read_only=True,
    )
