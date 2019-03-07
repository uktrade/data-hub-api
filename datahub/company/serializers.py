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
    AddressSerializer,
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


class NestedCompaniesHouseCompanySerializerV3(serializers.ModelSerializer):
    """
    Nested Companies House company serializer V3.

    TODO: delete once the migration to v4 is complete
    """

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


class CompaniesHouseCompanySerializerV3(NestedCompaniesHouseCompanySerializerV3):
    """
    Full Companies House company serializer V3.

    TODO: delete once the migration to v4 is complete
    """

    business_type = NestedRelatedField('metadata.BusinessType')

    class Meta(NestedCompaniesHouseCompanySerializerV3.Meta):
        fields = (
            *NestedCompaniesHouseCompanySerializerV3.Meta.fields,
            'business_type',
        )
        read_only_fields = fields


class CompaniesHouseCompanySerializerV4(serializers.ModelSerializer):
    """Companies House company serializer V4."""

    registered_address = AddressSerializer(
        source_model=CompaniesHouseCompany,
        address_source_prefix='registered_address',
    )
    business_type = NestedRelatedField('metadata.BusinessType')

    class Meta:
        model = CompaniesHouseCompany
        fields = (
            'id',
            'business_type',
            'company_category',
            'company_number',
            'company_status',
            'incorporation_date',
            'name',
            'registered_address',
            'sic_code_1',
            'sic_code_2',
            'sic_code_3',
            'sic_code_4',
            'uri',
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


class BaseCompanySerializer(PermittedFieldsModelSerializer):
    """
    Base Company read/write serializer

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

    archived_by = NestedAdviserField(read_only=True)
    business_type = NestedRelatedField(
        meta_models.BusinessType, required=False, allow_null=True,
    )
    one_list_group_tier = serializers.SerializerMethodField()
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
            'trading_names',
            'uk_based',
            'company_number',
            'vat_number',
            'duns_number',
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
            'business_type',
            'one_list_group_tier',
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
        dnb_read_only_fields = (
            'name',
            'trading_names',
            'company_number',
            'vat_number',
            'website',
            'business_type',
            'employee_range',
            'turnover_range',
            'headquarter_type',
            'global_headquarters',
        )
        validators = (
            RequiredUnlessAlreadyBlankValidator('sector', 'business_type'),
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
        )
        permissions = {
            f'company.{CompanyPermission.view_company_document}': 'archived_documents_url_path',
        }


class CompanySerializerV3(BaseCompanySerializer):
    """
    Company read/write serializer V3

    TODO: delete once the migration to address and registered address is complete
    """

    default_error_messages = {
        'uk_establishment_not_in_uk': ugettext_lazy(
            'A UK establishment (branch of non-UK company) must be in the UK.',
        ),
    }

    ADDRESS_FIELDS_MAPPING = {
        'trading': {
            'address_1': 'trading_address_1',
            'address_2': 'trading_address_2',
            'address_town': 'trading_address_town',
            'address_county': 'trading_address_county',
            'address_postcode': 'trading_address_postcode',
            'address_country': 'trading_address_country',
        },
        'registered': {
            'address_1': 'registered_address_1',
            'address_2': 'registered_address_2',
            'address_town': 'registered_address_town',
            'address_county': 'registered_address_county',
            'address_postcode': 'registered_address_postcode',
            'address_country': 'registered_address_country',
        },
    }

    companies_house_data = NestedCompaniesHouseCompanySerializerV3(read_only=True)
    registered_address_1 = serializers.CharField(max_length=MAX_LENGTH)
    registered_address_town = serializers.CharField(max_length=MAX_LENGTH)
    registered_address_country = NestedRelatedField(meta_models.Country)
    trading_address_country = NestedRelatedField(
        meta_models.Country, required=False, allow_null=True,
    )

    def validate(self, data):
        """
        Performs cross-field validation and adds extra fields to data.
        """
        data = super().validate(data)

        combiner = DataCombiner(self.instance, data)
        self._populate_address_fields(combiner, data)

        return data

    def _populate_address_fields(self, combiner, data):
        """
        Populates the address_* fields with the values from trading address or
        registered address whichever is defined.

        It's only triggered when any of the address fields are specified so that we don't
        accidentally run this logic when changing any other field.
        Doing this will allow us to implement a variant that updates the addresses
        in a different way.
        """
        all_address_field_names = {
            field
            for mapping in self.ADDRESS_FIELDS_MAPPING.values()
            for field in mapping.values()
        }

        # was any address field specified?
        if not all_address_field_names & data.keys():
            return

        trading_fields_mapping = Company.TRADING_ADDRESS_VALIDATION_MAPPING

        has_valid_trading_address = all(
            combiner.get_value(field_name)
            for field_name, rules in trading_fields_mapping.items()
            if rules['required']
        )

        mapping_source = 'trading' if has_valid_trading_address else 'registered'

        mapping = self.ADDRESS_FIELDS_MAPPING[mapping_source]
        for target_field_name, source_field_name in mapping.items():
            target_value = combiner.get_value(source_field_name)
            data[target_field_name] = target_value

    class Meta(BaseCompanySerializer.Meta):
        fields = (
            *BaseCompanySerializer.Meta.fields,

            'companies_house_data',
            'registered_address_1',
            'registered_address_2',
            'registered_address_town',
            'registered_address_county',
            'registered_address_postcode',
            'registered_address_country',
            'trading_address_1',
            'trading_address_2',
            'trading_address_town',
            'trading_address_county',
            'trading_address_postcode',
            'trading_address_country',
        )
        dnb_read_only_fields = (
            *BaseCompanySerializer.Meta.dnb_read_only_fields,

            'registered_address_1',
            'registered_address_2',
            'registered_address_town',
            'registered_address_county',
            'registered_address_postcode',
            'registered_address_country',
            'trading_address_1',
            'trading_address_2',
            'trading_address_town',
            'trading_address_county',
            'trading_address_postcode',
            'trading_address_country',
        )
        validators = (
            *BaseCompanySerializer.Meta.validators,
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
            ),
            AddressValidator(lazy=True, fields_mapping=Company.TRADING_ADDRESS_VALIDATION_MAPPING),
        )


class CompanySerializerV4(BaseCompanySerializer):
    """Company read/write serializer V4."""

    # TODO: delete once the migration to address and registered address is complete
    ADDRESS_FIELDS_MAPPING = {
        'address_1': 'trading_address_1',
        'address_2': 'trading_address_2',
        'address_town': 'trading_address_town',
        'address_county': 'trading_address_county',
        'address_postcode': 'trading_address_postcode',
        'address_country': 'trading_address_country',
    }

    default_error_messages = {
        'uk_establishment_not_in_uk': ugettext_lazy(
            'A UK establishment (branch of non-UK company) must be in the UK.',
        ),
    }

    address = AddressSerializer(source_model=Company, address_source_prefix='address')
    registered_address = AddressSerializer(
        source_model=Company,
        address_source_prefix='registered_address',
        required=False,
        allow_null=True,
    )

    def validate(self, data):
        """
        Performs cross-field validation and adds extra fields to data.
        """
        data = super().validate(data)

        combiner = DataCombiner(self.instance, data)
        self._populate_address_fields(combiner, data)

        return data

    def _populate_address_fields(self, combiner, data):
        """
        Populates the trading_address_* fields with the values from address.
        """
        # was any address field specified?
        if not self.ADDRESS_FIELDS_MAPPING.keys() & data.keys():
            return

        for source_field_name, target_field_name in self.ADDRESS_FIELDS_MAPPING.items():
            target_value = combiner.get_value(source_field_name)
            data[target_field_name] = target_value

    class Meta(BaseCompanySerializer.Meta):
        fields = (
            *BaseCompanySerializer.Meta.fields,

            'address',
            'registered_address',
        )
        dnb_read_only_fields = (
            *BaseCompanySerializer.Meta.dnb_read_only_fields,

            'address',
            'registered_address',
        )
        validators = (
            *BaseCompanySerializer.Meta.validators,

            RulesBasedValidator(
                ValidationRule(
                    'required',
                    OperatorRule('uk_region', bool),
                    when=EqualsRule(
                        'address_country',
                        Country.united_kingdom.value.id,
                    ),
                ),
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


class PublicCompanySerializer(CompanySerializerV4):
    """
    Read-only serialiser for the Hawk-authenticated company view.

    This is a slightly stripped down read-only version of the v4 company serialiser. Some fields
    containing personal data are deliberately omitted.
    """

    class Meta(CompanySerializerV4.Meta):
        fields = (
            'address',
            'archived',
            'archived_on',
            'archived_reason',
            'business_type',
            'company_number',
            'created_on',
            'description',
            'duns_number',
            'employee_range',
            'export_experience_category',
            'export_to_countries',
            'future_interest_countries',
            'global_headquarters',
            'headquarter_type',
            'id',
            'is_number_of_employees_estimated',
            'is_turnover_estimated',
            'modified_on',
            'name',
            'number_of_employees',
            'one_list_group_tier',
            'reference_code',
            'registered_address',
            'sector',
            'trading_names',
            'transfer_reason',
            'transferred_on',
            'transferred_to',
            'turnover',
            'turnover_range',
            'uk_based',
            'uk_region',
            'vat_number',
            'website',
        )
        permissions = {}
        read_only_fields = fields


class OneListCoreTeamMemberSerializer(serializers.Serializer):
    """One List Core Team Member Serializer."""

    adviser = NestedAdviserWithTeamGeographyField()
    is_global_account_manager = serializers.BooleanField()
