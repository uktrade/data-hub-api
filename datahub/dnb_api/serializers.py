from django.core.validators import integer_validator
from rest_framework import serializers

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import Company
from datahub.company.serializers import CompanySerializer
from datahub.company.validators import (
    has_no_invalid_company_number_characters,
    has_uk_establishment_number_prefix,
)
from datahub.core.constants import Country
from datahub.core.serializers import PermittedFieldsModelSerializer
from datahub.core.validators import EqualsRule, OperatorRule, RulesBasedValidator, ValidationRule
from datahub.interaction.models import InteractionPermission


class DNBMatchedCompanySerializer(PermittedFieldsModelSerializer):
    """
    Serialiser for data hub companies matched with a DNB entry.
    """

    latest_interaction = serializers.SerializerMethodField()

    def get_latest_interaction(self, obj):
        """
        Construct a latest interaction object from the latest_interaction_id,
        latest_interaction_date and latest_interaction_subject query set annotations.
        """
        if not obj.latest_interaction_id:
            return None

        return {
            'id': obj.latest_interaction_id,
            'created_on': obj.latest_interaction_created_on,
            # For consistency with the main interaction API, only return the date part.
            # See InteractionSerializer for more information
            'date': obj.latest_interaction_date.date(),
            'subject': obj.latest_interaction_subject,
        }

    class Meta:
        model = Company
        fields = (
            'id',
            'latest_interaction',
        )
        permissions = {
            f'interaction.{InteractionPermission.view_all}': 'latest_interaction',
        }


class DNBCompanySerializer(CompanySerializer):
    """
    For creating a company from DNB data.

    Essentially makes the DNB fields writable and removes the validators
    that make: sector, business_type and uk_region fields required.

    TODO: The validators would be put back in when we have done the work for
    unpacking these fields from the DNB payload so this particular change
    is temporary.
    """

    duns_number = serializers.CharField(
        max_length=9,
        min_length=9,
        validators=(integer_validator,),
    )

    global_ultimate_duns_number = serializers.CharField(
        allow_blank=True,
        max_length=9,
        min_length=9,
        validators=(integer_validator, ),
    )

    class Meta(CompanySerializer.Meta):
        read_only_fields = []
        dnb_read_only_fields = []
        validators = (
            RulesBasedValidator(
                ValidationRule(
                    'required',
                    OperatorRule('company_number', bool),
                    when=EqualsRule(
                        'business_type',
                        BusinessTypeConstant.uk_establishment.value.id,
                    ),
                ),
                ValidationRule(
                    'invalid_uk_establishment_number_characters',
                    OperatorRule('company_number', has_no_invalid_company_number_characters),
                    when=EqualsRule(
                        'business_type',
                        BusinessTypeConstant.uk_establishment.value.id,
                    ),
                ),
                ValidationRule(
                    'invalid_uk_establishment_number_prefix',
                    OperatorRule('company_number', has_uk_establishment_number_prefix),
                    when=EqualsRule(
                        'business_type',
                        BusinessTypeConstant.uk_establishment.value.id,
                    ),
                ),
            ),
            RulesBasedValidator(
                ValidationRule(
                    'uk_establishment_not_in_uk',
                    EqualsRule('address_country', Country.united_kingdom.value.id),
                    when=EqualsRule(
                        'business_type',
                        BusinessTypeConstant.uk_establishment.value.id,
                    ),
                ),
            ),
        )


class DUNSNumberSerializer(serializers.Serializer):
    """
    Parses duns_number from request body and validates format.
    """

    duns_number = serializers.CharField(
        write_only=True,
        max_length=9,
        min_length=9,
        validators=(integer_validator,),
    )

    def validate_duns_number(self, duns_number):
        """
        Check if the duns_number is valid i.e. isn't already assigned
        to another company.
        """
        if Company.objects.filter(duns_number=duns_number).exists():
            raise serializers.ValidationError(
                f'Company with duns_number: {duns_number} already exists in DataHub.',
            )
        return duns_number


class DNBInvestigationDataSerializer(serializers.Serializer):
    """
    Serializer for DNBInvestigationData - a JSON field that contains
    auxuliary data needed for submitting to DNB for investigation.
    """

    telephone_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class DNBCompanyInvestigationSerializer(CompanySerializer):
    """
    For creating Company record to be investigated by DNB.

    Sets `dnb_investigation_data`.
    """

    dnb_investigation_data = serializers.JSONField(
        required=False,
        allow_null=True,
        write_only=True,
    )

    def validate_dnb_investigation_data(self, dnb_investigation_data):
        """
        Check if dnb_investigation_data is valid.
        """
        if dnb_investigation_data in (None, ''):
            return None
        serializer = DNBInvestigationDataSerializer(data=dnb_investigation_data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def validate(self, data):
        """
        Validate if either website or telephone_number is present.
        """
        data = super().validate(data)
        investigation_data = data.get('dnb_investigation_data') or {}

        if (
            data.get('website') in (None, '')
            and investigation_data.get('telephone_number') in (None, '')
        ):
            raise serializers.ValidationError(
                f'Either website or telephone_number must be provided.',
            )

        return data

    class Meta(CompanySerializer.Meta):
        fields = CompanySerializer.Meta.fields + ('dnb_investigation_data', )
