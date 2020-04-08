from urllib.parse import urlparse

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
from datahub.core.serializers import (
    NestedRelatedField,
    PermittedFieldsModelSerializer,
    RelaxedURLField,
)
from datahub.core.validators import EqualsRule, OperatorRule, RulesBasedValidator, ValidationRule
from datahub.interaction.models import InteractionPermission
from datahub.metadata.models import Country as CountryModel


class SerializerNotPartial(Exception):
    """
    Exception for when some logic was called which expects a serializer object
    to be self.partial=True.
    """


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

    def partial_save(self, **kwargs):
        """
        Method to save the instance - by writing only the fields updated by the serializer.
        Takes kwargs to override the values of specific fields for the model on save.

        Note: modified_on will not be updated by this method - this is the original
        reason for this method to exist as modified_on has auto_now=True and which makes it
        difficult to to prevent updates to this field.
        """
        if not self.partial:
            raise SerializerNotPartial(
                'partial_save() called, but serializer is not set as partial.',
            )
        instance = self.instance
        validated_data = {**self.validated_data, **kwargs}
        for field, value in validated_data.items():
            setattr(instance, field, value)
        update_fields = validated_data.keys()
        instance.save(update_fields=update_fields)


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


# TODO: Remove this once the D&B investigations endpoint has been released
class LegacyDNBInvestigationDataSerializer(serializers.Serializer):
    """
    Serializer for DNBInvestigationData - a JSON field that contains
    auxuliary data needed for submitting to DNB for investigation.
    """

    telephone_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )


# TODO: Refactor this once the D&B investigations endpoint has been released
class LegacyDNBCompanyInvestigationSerializer(CompanySerializer):
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
        serializer = LegacyDNBInvestigationDataSerializer(data=dnb_investigation_data)
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


class DNBCompanyLinkSerializer(DUNSNumberSerializer):
    """
    Validate POST data for DNBCompanyLinkView.
    """

    company_id = NestedRelatedField('company.Company', required=True)


class DNBAddressSerializer(serializers.Serializer):
    """
    Validate address and convert it to the format expected by dnb-service.
    """

    line_1 = serializers.CharField(source='address_line_1')
    line_2 = serializers.CharField(source='address_line_2', required=False)
    town = serializers.CharField(source='address_town')
    county = serializers.CharField(source='address_county', required=False)
    postcode = serializers.CharField(source='address_postcode', required=False)
    country = NestedRelatedField(model=CountryModel, source='address_country')

    def validate_country(self, country):
        """
        Return iso_alpha2_code only.
        """
        return country.iso_alpha2_code


class AddressRequestSerializer(DNBAddressSerializer):
    """
    Validate address and convert it to the format expected by dnb-service.
    """

    line_1 = serializers.CharField(source='address_line_1', required=False)
    town = serializers.CharField(source='address_town', required=False)
    country = NestedRelatedField(model=CountryModel, source='address_country', required=False)


class ChangeRequestSerializer(serializers.Serializer):
    """
    Validate change requests and convert it to the format expected by dnb-service.
    """

    name = serializers.CharField(source='primary_name', required=False)
    trading_names = serializers.ListField(required=False)
    number_of_employees = serializers.IntegerField(source='employee_number', required=False)
    turnover = serializers.IntegerField(source='annual_sales', required=False)
    address = AddressRequestSerializer(required=False)
    website = RelaxedURLField(source='domain', required=False)

    def validate_website(self, website):
        """
        Change website to domain.
        """
        return urlparse(website).netloc


class DNBCompanyChangeRequestSerializer(serializers.Serializer):
    """
    Validate POST data for DNBCompanyChangeRequestView and convert it to the format
    expected by dnb-service.
    """

    duns_number = serializers.CharField(
        max_length=9,
        min_length=9,
        validators=(integer_validator,),
    )

    changes = ChangeRequestSerializer()

    def validate_duns_number(self, duns_number):
        """
        Validate duns_number.
        """
        try:
            company = Company.objects.get(duns_number=duns_number)
        except Company.DoesNotExist:
            raise serializers.ValidationError(
                f'Company with duns_number: {duns_number} does not exists in DataHub.',
            )
        self.company = company
        return duns_number

    def validate_changes(self, changes):
        """
        Changes should not be empty.
        """
        if not changes:
            raise serializers.ValidationError(
                f'No changes submitted.',
            )
        return changes

    def validate(self, data):
        """
        Augment address changes with unchanged address fields and un-nest address changes.
        """
        address_changes = data['changes'].pop('address', {})
        if address_changes:
            data['changes'] = {
                **data['changes'],
                **{
                    'address_line_1': self.company.address_1,
                    'address_line_2': self.company.address_2,
                    'address_town': self.company.address_town,
                    'address_county': self.company.address_county,
                    'address_country': self.company.address_country.iso_alpha2_code,
                    'address_postcode': self.company.address_postcode,
                },
                **address_changes,
            }

        return data


class DNBCompanyInvestigationSerializer(serializers.Serializer):
    """
    Validate POST data for DNBCompanyInvestigationView and convert it to the format
    expected by dnb-service.
    """

    company = NestedRelatedField(Company)
    name = serializers.CharField(source='primary_name')
    address = DNBAddressSerializer()
    website = RelaxedURLField(
        source='domain',
        required=False,
        allow_blank=True,
    )
    telephone_number = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate_website(self, website):
        """
        Change website to domain.
        """
        return urlparse(website).netloc

    def validate(self, data):
        """
        Validate if either website or telephone_number is present.
        """
        data = super().validate(data)

        if (
            data.get('website') in (None, '')
            and data.get('telephone_number') in (None, '')
        ):
            raise serializers.ValidationError(
                'Either website or telephone_number must be provided.',
            )

        address_data = data.pop('address', {})
        return {
            **data,
            **address_data,
        }
