from functools import partial
from operator import not_
from uuid import UUID

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import (
    Advisor,
    CompaniesHouseCompany,
    Company,
    CompanyPermission,
    Contact,
    ContactPermission,
    ExportExperienceCategory,
    OneListTier,
)
from datahub.company.validators import (
    has_no_invalid_company_number_characters,
    has_uk_establishment_number_prefix,
)
from datahub.core.constants import Country
from datahub.core.constants import HeadquarterType
from datahub.core.serializers import (
    NestedRelatedField,
    PermittedFieldsModelSerializer,
    RelaxedURLField,
)
from datahub.core.validate_utils import DataCombiner
from datahub.core.validators import (
    AddressValidator,
    AllIsBlankRule,
    AnyIsNotBlankRule,
    EqualsRule,
    NotArchivedValidator,
    OperatorRule,
    RequiredUnlessAlreadyBlankValidator,
    RulesBasedValidator,
    ValidationRule,
)
from datahub.metadata import models as meta_models
from datahub.metadata.serializers import TeamWithGeographyField


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


NestedAdviserField = partial(
    NestedRelatedField,
    'company.Advisor',
    extra_fields=(
        'name',
        'first_name',
        'last_name',
    ),
)


NestedAdviserWithTeamField = partial(
    NestedRelatedField,
    'company.Advisor',
    extra_fields=(
        'name',
        'first_name',
        'last_name',
        ('dit_team', NestedRelatedField('metadata.Team')),
    ),
)

# like NestedAdviserField but includes dit_team with uk_region and country
NestedAdviserWithTeamGeographyField = partial(
    NestedRelatedField,
    'company.Advisor',
    extra_fields=(
        'name',
        'first_name',
        'last_name',
        ('dit_team', TeamWithGeographyField()),
    ),
)


class _ArrayAsSingleItemField(serializers.CharField):
    """
    Serialiser field that makes an ArrayField behave like a CharField.
    Use for temporary backwards compatibility when migrating a CharField to be an ArrayField.

    This isn't intended to be used in any other way as if the ArrayField contains multiple
    items, only one of them will be returned, and all of them will be overwritten on updates.

    TODO Remove this once trading_name has been removed from the API.
    """

    def run_validation(self, data=serializers.empty):
        """
        Converts a user-provided value to a list containing that value after it has been validated.

        This logic is here instead of in to_internal_value so that we can keep the original
        validators (for CharField instead of ArrayField).
        Also, to_internal_value is not called in case of empty data which is problematic.
        """
        value = super().run_validation(data)
        if not value:
            return []
        return [value]

    def to_representation(self, value):
        """Converts a list of values to the representation of the first item."""
        if not value:
            return ''
        return super().to_representation(value[0])


class AdviserSerializer(serializers.ModelSerializer):
    """Adviser serializer."""

    name = serializers.CharField()

    class Meta:
        model = Advisor
        fields = (
            'id',
            'name',
            'is_active',
            'last_login',
            'first_name',
            'last_name',
            'email',
            'contact_email',
            'telephone_number',
            'dit_team',
        )
        depth = 1


class NestedCompaniesHouseCompanySerializer(serializers.ModelSerializer):
    """Nested Companies House company serializer."""

    registered_address_country = NestedRelatedField('metadata.Country')

    class Meta:
        model = CompaniesHouseCompany
        fields = (
            'id',
            'company_category',
            'company_number',
            'company_status',
            'incorporation_date',
            'name',
            'registered_address_1',
            'registered_address_2',
            'registered_address_county',
            'registered_address_country',
            'registered_address_town',
            'registered_address_postcode',
            'sic_code_1',
            'sic_code_2',
            'sic_code_3',
            'sic_code_4',
            'uri',
        )
        read_only_fields = fields


class CompaniesHouseCompanySerializer(NestedCompaniesHouseCompanySerializer):
    """Full Companies House company serializer."""

    business_type = NestedRelatedField('metadata.BusinessType')

    class Meta(NestedCompaniesHouseCompanySerializer.Meta):
        fields = (
            *NestedCompaniesHouseCompanySerializer.Meta.fields,
            'business_type',
        )
        read_only_fields = fields


class ContactSerializer(PermittedFieldsModelSerializer):
    """Contact serializer for writing operations V3."""

    default_error_messages = {
        'address_same_as_company_and_has_address': ugettext_lazy(
            'Please select either address_same_as_company or enter an address manually, not both!',
        ),
        'no_address': ugettext_lazy(
            'Please select either address_same_as_company or enter an address manually.',
        ),
    }

    title = NestedRelatedField(
        meta_models.Title, required=False, allow_null=True,
    )
    company = NestedRelatedField(
        Company, required=False, allow_null=True,
    )
    adviser = NestedAdviserField(read_only=True)
    address_country = NestedRelatedField(
        meta_models.Country, required=False, allow_null=True,
    )
    archived = serializers.BooleanField(read_only=True)
    archived_on = serializers.DateTimeField(read_only=True)
    archived_reason = serializers.CharField(read_only=True)
    archived_by = NestedAdviserField(read_only=True)
    primary = serializers.BooleanField()

    class Meta:
        model = Contact
        fields = (
            'id',
            'title',
            'first_name',
            'last_name',
            'name',
            'job_title',
            'company',
            'adviser',
            'primary',
            'telephone_countrycode',
            'telephone_number',
            'email',
            'address_same_as_company',
            'address_1',
            'address_2',
            'address_town',
            'address_county',
            'address_country',
            'address_postcode',
            'telephone_alternative',
            'email_alternative',
            'notes',
            'accepts_dit_email_marketing',
            'archived',
            'archived_documents_url_path',
            'archived_on',
            'archived_reason',
            'archived_by',
            'created_on',
            'modified_on',
        )
        read_only_fields = (
            'archived_documents_url_path',
        )
        validators = [
            NotArchivedValidator(),
            RulesBasedValidator(
                ValidationRule(
                    'address_same_as_company_and_has_address',
                    OperatorRule('address_same_as_company', not_),
                    when=AnyIsNotBlankRule(*Contact.ADDRESS_VALIDATION_MAPPING.keys()),
                ),
                ValidationRule(
                    'no_address',
                    OperatorRule('address_same_as_company', bool),
                    when=AllIsBlankRule(*Contact.ADDRESS_VALIDATION_MAPPING.keys()),
                ),
            ),
            # Note: This is deliberately after RulesBasedValidator, so that
            # address_same_as_company rules run first.
            AddressValidator(lazy=True, fields_mapping=Contact.ADDRESS_VALIDATION_MAPPING),
        ]
        permissions = {
            f'company.{ContactPermission.view_contact_document}': 'archived_documents_url_path',
        }


class CompanySerializer(PermittedFieldsModelSerializer):
    """
    Company read/write serializer V3.

    Note that there is special validation for company number for UK establishments. This is
    because we don't get UK establishments in our Companies House data file at present, so users
    have to enter company numbers for UK establishments manually.
    """

    default_error_messages = {
        'invalid_uk_establishment_number_prefix': ugettext_lazy(
            'This must be a valid UK establishment number, beginning with BR.',
        ),
        'invalid_uk_establishment_number_characters': ugettext_lazy(
            'This field can only contain the letters A to Z and numbers (no symbols, punctuation '
            'or spaces).',
        ),
        'uk_establishment_not_in_uk': ugettext_lazy(
            'A UK establishment (branch of non-UK company) must be in the UK.',
        ),
        'global_headquarters_hq_type_is_not_global_headquarters': ugettext_lazy(
            'Company to be linked as global headquarters must be a global headquarters.',
        ),
        'invalid_global_headquarters': ugettext_lazy(
            'Global headquarters cannot point to itself.',
        ),
        'global_headquarters_has_subsidiaries': ugettext_lazy(
            'Subsidiaries have to be unlinked before changing headquarter type.',
        ),
        'subsidiary_cannot_be_a_global_headquarters': ugettext_lazy(
            'A company cannot both be and have a global headquarters.',
        ),
    }

    registered_address_country = NestedRelatedField(meta_models.Country)
    trading_name = _ArrayAsSingleItemField(
        source='trading_names',
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=MAX_LENGTH,
    )
    trading_address_country = NestedRelatedField(
        meta_models.Country, required=False, allow_null=True,
    )
    archived_by = NestedAdviserField(read_only=True)
    business_type = NestedRelatedField(
        meta_models.BusinessType, required=False, allow_null=True,
    )
    one_list_group_tier = serializers.SerializerMethodField()
    companies_house_data = NestedCompaniesHouseCompanySerializer(read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    transferred_to = NestedRelatedField('company.Company', read_only=True)
    employee_range = NestedRelatedField(
        meta_models.EmployeeRange, required=False, allow_null=True,
    )
    export_to_countries = NestedRelatedField(
        meta_models.Country, many=True, required=False,
    )
    future_interest_countries = NestedRelatedField(
        meta_models.Country, many=True, required=False,
    )
    headquarter_type = NestedRelatedField(
        meta_models.HeadquarterType, required=False, allow_null=True,
    )
    one_list_group_global_account_manager = serializers.SerializerMethodField()
    global_headquarters = NestedRelatedField(
        'company.Company', required=False, allow_null=True,
    )
    sector = NestedRelatedField(meta_models.Sector, required=False, allow_null=True)
    turnover_range = NestedRelatedField(
        meta_models.TurnoverRange, required=False, allow_null=True,
    )
    uk_region = NestedRelatedField(
        meta_models.UKRegion, required=False, allow_null=True,
    )
    export_experience_category = NestedRelatedField(
        ExportExperienceCategory, required=False, allow_null=True,
    )

    # Use our RelaxedURLField instead to automatically fix URLs without a scheme
    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.URLField: RelaxedURLField,
    }

    def __init__(self, *args, **kwargs):
        """
        Make some of the fields read_only if the instance has a duns_number set.
        This is because those values come from an external source
        and we don't want users to override them.
        """
        super().__init__(*args, **kwargs)
        if self.instance and not isinstance(self.instance, list) and self.instance.duns_number:
            for field in self.Meta.dnb_read_only_fields:
                self.fields[field].read_only = True

    def validate(self, data):
        """
        Performs cross-field validation and adds extra fields to data.
        """
        combiner = DataCombiner(self.instance, data)

        if {'global_headquarters', 'headquarter_type'} & data.keys():
            headquarter_type_id = combiner.get_value_id('headquarter_type')
            global_headquarters_id = combiner.get_value_id('global_headquarters')
            if (
                headquarter_type_id is not None
                and UUID(headquarter_type_id) == UUID(HeadquarterType.ghq.value.id)
                and global_headquarters_id is not None
            ):
                message = self.error_messages['subsidiary_cannot_be_a_global_headquarters']
                raise serializers.ValidationError({
                    'headquarter_type': message,
                })

        # TODO: remove after the alias column is deleted

        # Save the first item in trading_names in alias if specified.
        if 'trading_names' in data:
            trading_names = data['trading_names']
            data['alias'] = '' if not trading_names else trading_names[0]

        return data

    def validate_headquarter_type(self, headquarter_type):
        """Raises an exception if company is a global hq and has subsidiaries."""
        if self.instance is None:
            return headquarter_type

        headquarter_type_id = getattr(headquarter_type, 'id', None)

        if (
            self.instance.headquarter_type_id != headquarter_type_id
            and self.instance.headquarter_type_id == UUID(HeadquarterType.ghq.value.id)
            and self.instance.subsidiaries.exists()
        ):
            raise serializers.ValidationError(
                self.error_messages['global_headquarters_has_subsidiaries'],
            )

        return headquarter_type

    def validate_global_headquarters(self, global_headquarters):
        """
        Ensure that global headquarters is global headquarters and it is not pointing
        at the model itself.
        """
        if global_headquarters:
            # checks if global_headquarters is not pointing to an instance of the model
            if self.instance == global_headquarters:
                raise serializers.ValidationError(
                    self.error_messages['invalid_global_headquarters'],
                )

            # checks if global_headquarters is global_headquarters
            if global_headquarters.headquarter_type_id != UUID(HeadquarterType.ghq.value.id):
                raise serializers.ValidationError(
                    self.error_messages[
                        'global_headquarters_hq_type_is_not_global_headquarters'
                    ],
                )

        return global_headquarters

    def get_one_list_group_tier(self, obj):
        """
        :returns: the One List Tier for the group that company `obj` is part of.
        """
        one_list_tier = obj.get_one_list_group_tier()

        field = NestedRelatedField(OneListTier)
        return field.to_representation(one_list_tier)

    def get_one_list_group_global_account_manager(self, obj):
        """
        :returns: the One List Global Account Manager for the group that company `obj` is part of.
        """
        global_account_manager = obj.get_one_list_group_global_account_manager()

        field = NestedAdviserWithTeamGeographyField()
        return field.to_representation(global_account_manager)

    class Meta:
        model = Company
        fields = (
            'id',
            'reference_code',
            'name',
            'trading_name',
            'trading_names',
            'uk_based',
            'company_number',
            'vat_number',
            'duns_number',
            'registered_address_1',
            'registered_address_2',
            'registered_address_town',
            'registered_address_county',
            'registered_address_postcode',
            'registered_address_country',
            'created_on',
            'modified_on',
            'archived',
            'archived_documents_url_path',
            'archived_on',
            'archived_reason',
            'archived_by',
            'description',
            'transferred_by',
            'transferred_on',
            'transferred_to',
            'transfer_reason',
            'website',
            'trading_address_1',
            'trading_address_2',
            'trading_address_town',
            'trading_address_county',
            'trading_address_postcode',
            'trading_address_country',
            'business_type',
            'one_list_group_tier',
            'companies_house_data',
            'contacts',
            'employee_range',
            'number_of_employees',
            'is_number_of_employees_estimated',
            'export_to_countries',
            'future_interest_countries',
            'headquarter_type',
            'one_list_group_global_account_manager',
            'global_headquarters',
            'sector',
            'turnover_range',
            'turnover',
            'is_turnover_estimated',
            'uk_region',
            'export_experience_category',
        )
        read_only_fields = (
            'archived',
            'archived_documents_url_path',
            'archived_on',
            'archived_reason',
            'reference_code',
            'transfer_reason',
            'duns_number',
            'turnover',
            'is_turnover_estimated',
            'number_of_employees',
            'is_number_of_employees_estimated',
        )
        dnb_read_only_fields = [
            'name',
            'trading_name',
            'trading_names',
            'company_number',
            'vat_number',
            'registered_address_1',
            'registered_address_2',
            'registered_address_town',
            'registered_address_county',
            'registered_address_postcode',
            'registered_address_country',
            'website',
            'trading_address_1',
            'trading_address_2',
            'trading_address_town',
            'trading_address_county',
            'trading_address_postcode',
            'trading_address_country',
            'business_type',
            'employee_range',
            'turnover_range',
            'headquarter_type',
            'global_headquarters',
        ]
        validators = [
            RequiredUnlessAlreadyBlankValidator('sector', 'business_type'),
            RulesBasedValidator(
                ValidationRule(
                    'required',
                    OperatorRule('uk_region', bool),
                    when=EqualsRule(
                        'registered_address_country',
                        Country.united_kingdom.value.id,
                    ),
                ),
                ValidationRule(
                    'uk_establishment_not_in_uk',
                    EqualsRule('registered_address_country', Country.united_kingdom.value.id),
                    when=EqualsRule(
                        'business_type',
                        BusinessTypeConstant.uk_establishment.value.id,
                    ),
                ),
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
            AddressValidator(lazy=True, fields_mapping=Company.TRADING_ADDRESS_VALIDATION_MAPPING),
        ]
        permissions = {
            f'company.{CompanyPermission.view_company_document}': 'archived_documents_url_path',
        }


class OneListCoreTeamMemberSerializer(serializers.Serializer):
    """One List Core Team Member Serializer."""

    adviser = NestedAdviserWithTeamGeographyField()
    is_global_account_manager = serializers.BooleanField()
