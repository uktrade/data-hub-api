from rest_framework import serializers

from datahub.company.models import Company
from datahub.core.serializers import NestedRelatedField
from datahub.investor_profile.constants import ProfileType as ProfileTypeConstant
from datahub.investor_profile.models import (
    InvestorProfile,
    ProfileType,
)


BASE_FIELDS = [
    'id',
    'created_on',
    'modified_on',
    'investor_company',
    'profile_type',
]


class LargeCapitalInvestorProfileSerializer(serializers.ModelSerializer):
    """Large capital investor profile serializer"""

    investor_company = NestedRelatedField(
        Company,
        allow_null=False,
    )

    profile_type = NestedRelatedField(
        ProfileType,
        read_only=True,
    )

    created_on = serializers.DateTimeField(
        read_only=True,
    )

    modified_on = serializers.DateTimeField(
        read_only=True,
    )

    def validate_investor_company(self, value):
        """Validates the company does not already have a large capital investment profile"""
        if value.investor_profiles.filter(
                profile_type_id=ProfileTypeConstant.large.value.id,
        ).exists():
            raise serializers.ValidationError(
                'Investor company already has large capital investor profile',
            )
        return value

    class Meta:
        model = InvestorProfile
        fields = BASE_FIELDS
