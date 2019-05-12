from django.utils.translation import gettext_lazy
from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Company
from datahub.core.serializers import ConstantModelSerializer, NestedRelatedField
from datahub.core.validate_utils import is_not_blank
from datahub.core.validators import (
    AnyIsNotBlankRule,
    InRule,
    OperatorRule,
    RulesBasedValidator,
    ValidationRule,
)
from datahub.investment.investor_profile.constants import (
    REQUIRED_CHECKS_THAT_DO_NOT_NEED_ADDITIONAL_INFORMATION,
    REQUIRED_CHECKS_THAT_NEED_ADDITIONAL_INFORMATION,
)
from datahub.investment.investor_profile.models import (
    AssetClassInterest,
    AssetClassInterestSector,
    ConstructionRisk,
    DealTicketSize,
    DesiredDealRole,
    EquityPercentage,
    InvestorType,
    LargeCapitalInvestmentType,
    LargeCapitalInvestorProfile,
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

LARGE_CAPITAL_ADDITIONAL_DETAILS_FIELDS = [
    'required_checks_conducted_on',
    'required_checks_conducted_by',
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
    + LARGE_CAPITAL_ADDITIONAL_DETAILS_FIELDS
    + LARGE_CAPITAL_REQUIREMENTS_FIELDS
    + LARGE_CAPITAL_LOCATION_FIELDS
)


class LargeCapitalInvestorProfileSerializer(serializers.ModelSerializer):
    """Large capital investor profile serializer."""

    default_error_messages = {
        'invalid_required_checks_conducted_on': gettext_lazy(
            'Enter the date of the most recent checks',
        ),
        'invalid_required_checks_conducted_by': gettext_lazy(
            'Enter the person responsible for the most recent checks',
        ),
        'required_checks_conducted_value': gettext_lazy(
            'Enter a value for required checks conducted',
        ),
    }

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
        allow_null=True,
    )

    required_checks_conducted = NestedRelatedField(
        RequiredChecksConducted,
        required=False,
    )

    required_checks_conducted_by = NestedRelatedField(
        'company.Advisor',
        required=False,
    )

    required_checks_conducted_on = serializers.DateField(
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
        allow_null=True,
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
        allow_null=True,
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
        queryset = value.investor_profiles.all()
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError(
                'Investor company already has large capital investor profile',
            )
        return value

    def update(self, instance, validated_data):
        """Overriding update to check required checks conducted data."""
        validated_data = self._update_required_checks_conducted(validated_data)
        return super().update(instance, validated_data)

    def _update_required_checks_conducted(self, validated_data):
        """
        Checks if required checks conducted is being set to a setting that does not require
        the conditional data. If it is then the conditional fields are blanked.
        """
        if 'required_checks_conducted' in validated_data:
            if (
                    str(validated_data['required_checks_conducted'].id)
                    in REQUIRED_CHECKS_THAT_DO_NOT_NEED_ADDITIONAL_INFORMATION
            ):
                validated_data['required_checks_conducted_on'] = None
                validated_data['required_checks_conducted_by'] = None
        return validated_data

    class Meta:
        model = LargeCapitalInvestorProfile
        fields = ALL_LARGE_CAPITAL_FIELDS
        validators = [
            RulesBasedValidator(
                ValidationRule(
                    'invalid_required_checks_conducted_on',
                    OperatorRule('required_checks_conducted_on', bool),
                    when=InRule(
                        'required_checks_conducted',
                        REQUIRED_CHECKS_THAT_NEED_ADDITIONAL_INFORMATION,
                    ),
                ),
                ValidationRule(
                    'invalid_required_checks_conducted_by',
                    OperatorRule('required_checks_conducted_by', bool),
                    when=InRule(
                        'required_checks_conducted',
                        REQUIRED_CHECKS_THAT_NEED_ADDITIONAL_INFORMATION,
                    ),
                ),
                ValidationRule(
                    'required_checks_conducted_value',
                    OperatorRule('required_checks_conducted', is_not_blank),
                    when=AnyIsNotBlankRule(
                        'required_checks_conducted_by',
                        'required_checks_conducted_on',
                    ),
                ),
            ),
        ]


class AssetClassInterestSerializer(ConstantModelSerializer):
    """Asset class interest serializer."""

    asset_class_interest_sector = NestedRelatedField(
        AssetClassInterestSector,
        read_only=True,
    )
