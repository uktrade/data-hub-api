from functools import partial
from operator import not_
from uuid import UUID

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import (
    Advisor, CompaniesHouseCompany, Company, CompanyPermission,
    Contact, ContactPermission, ExportExperienceCategory,
)
from datahub.company.validators import (
    has_no_invalid_company_number_characters,
    has_uk_establishment_number_prefix,
)
from datahub.core.constants import Country
from datahub.core.constants import HeadquarterType
from datahub.core.serializers import (
    NestedRelatedField, PermittedFieldsModelSerializer, RelaxedURLField
)
from datahub.core.validate_utils import DataCombiner
from datahub.core.validators import (
    AddressValidator,
    AllIsBlankRule,
    AnyIsNotBlankRule,
    EqualsRule,
    OperatorRule,
    RequiredUnlessAlreadyBlankValidator,
    RulesBasedValidator,
    ValidationRule,
)
from datahub.metadata import models as meta_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


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


NestedAdviserField = partial(
    NestedRelatedField, 'company.Advisor',
    extra_fields=('first_name', 'last_name', 'name')
)


class ContactSerializer(PermittedFieldsModelSerializer):
    """Contact serializer for writing operations V3."""

    default_error_messages = {
        'contact_preferences_required': ugettext_lazy(
            'A contact should have at least one way of being contacted. Please select either '
            'email or phone, or both.'
        ),
        'address_same_as_company_and_has_address': ugettext_lazy(
            'Please select either address_same_as_company or enter an address manually, not both!'
        ),
        'no_address': ugettext_lazy(
            'Please select either address_same_as_company or enter an address manually.'
        ),
    }

    title = NestedRelatedField(
        meta_models.Title, required=False, allow_null=True
    )
    company = NestedRelatedField(
        Company, required=False, allow_null=True
    )
    adviser = NestedAdviserField(read_only=True)
    address_country = NestedRelatedField(
        meta_models.Country, required=False, allow_null=True
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
            'contactable_by_dit',
            'contactable_by_uk_dit_partners',
            'contactable_by_overseas_dit_partners',
            'accepts_dit_email_marketing',
            'contactable_by_email',
            'contactable_by_phone',
            'archived',
            'archived_documents_url_path',
            'archived_on',
            'archived_reason',
            'archived_by',
            'created_on',
            'modified_on'
        )
        read_only_fields = (
            'archived_documents_url_path',
        )
        validators = [
            RulesBasedValidator(
                ValidationRule(
                    'contact_preferences_required',
                    OperatorRule('contactable_by_email', bool),
                    when=OperatorRule('contactable_by_phone', not_),
                ),
                ValidationRule(
                    'contact_preferences_required',
                    OperatorRule('contactable_by_phone', bool),
                    when=OperatorRule('contactable_by_email', not_),
                ),
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
            AddressValidator(lazy=True, fields_mapping=Contact.ADDRESS_VALIDATION_MAPPING)
        ]
        extra_kwargs = {
            'contactable_by_email': {'default': True},
            'contactable_by_phone': {'default': True},
        }
        permissions = {
            f'company.{ContactPermission.read_contact_document}': 'archived_documents_url_path',
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
            'This must be a valid UK establishment number, beginning with BR.'
        ),
        'invalid_uk_establishment_number_characters': ugettext_lazy(
            'This field can only contain the letters A to Z and numbers (no symbols, punctuation '
            'or spaces).'
        ),
        'uk_establishment_not_in_uk': ugettext_lazy(
            'A UK establishment (branch of non-UK company) must be in the UK.'
        ),
        'headquarter_type_is_not_global_headquarters': ugettext_lazy(
            'Company to be linked as global headquarters must be a global headquarters.'
        ),
        'invalid_global_headquarters': ugettext_lazy(
            'Global headquarters cannot point to itself.'
        ),
        'global_headquarters_has_subsidiaries': ugettext_lazy(
            'Subsidiaries have to be unlinked before changing headquarter type.',
        ),
        'subsidiary_cannot_be_a_global_headquarters': ugettext_lazy(
            'A company cannot both be and have a global headquarters.',
        ),
    }

    registered_address_country = NestedRelatedField(meta_models.Country)
    trading_name = serializers.CharField(
        source='alias', required=False, allow_null=True, allow_blank=True, max_length=MAX_LENGTH
    )
    trading_address_country = NestedRelatedField(
        meta_models.Country, required=False, allow_null=True
    )
    account_manager = NestedAdviserField(required=False, allow_null=True)
    archived_by = NestedAdviserField(read_only=True)
    business_type = NestedRelatedField(
        meta_models.BusinessType, required=False, allow_null=True
    )
    classification = NestedRelatedField(
        meta_models.CompanyClassification, required=False, allow_null=True
    )
    companies_house_data = NestedCompaniesHouseCompanySerializer(read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    employee_range = NestedRelatedField(
        meta_models.EmployeeRange, required=False, allow_null=True
    )
    export_to_countries = NestedRelatedField(
        meta_models.Country, many=True, required=False
    )
    future_interest_countries = NestedRelatedField(
        meta_models.Country, many=True, required=False
    )
    headquarter_type = NestedRelatedField(
        meta_models.HeadquarterType, required=False, allow_null=True
    )
    one_list_account_owner = NestedAdviserField(
        required=False, allow_null=True
    )
    global_headquarters = NestedRelatedField(
        'company.Company', required=False, allow_null=True
    )
    sector = NestedRelatedField(meta_models.Sector, required=False, allow_null=True)
    turnover_range = NestedRelatedField(
        meta_models.TurnoverRange, required=False, allow_null=True
    )
    uk_region = NestedRelatedField(
        meta_models.UKRegion, required=False, allow_null=True
    )
    investment_projects_invested_in = NestedRelatedField(
        'investment.InvestmentProject', many=True, read_only=True,
        extra_fields=('name', 'project_code'),
        source='investor_investment_projects'
    )
    investment_projects_invested_in_count = serializers.IntegerField(
        source='investor_investment_projects.count', read_only=True
    )
    export_experience_category = NestedRelatedField(
        ExportExperienceCategory, required=False, allow_null=True
    )

    # Use our RelaxedURLField instead to automatically fix URLs without a scheme
    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.URLField: RelaxedURLField,
    }

    def validate(self, data):
        """Performs cross-field validation."""
        errors = {}
        combiner = DataCombiner(self.instance, data)

        validators = (
            self._validate_cannot_become_ghq_if_linked_to_another_ghq,
            self._validate_cannot_remove_ghq_if_it_has_subsidiaries,
            self._validate_ghq_is_not_self,
            self._validate_ghq_has_ghq_headquarter_type,
        )

        for validator in validators:
            errors.update(validator(combiner))

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def _validate_cannot_remove_ghq_if_it_has_subsidiaries(self, combiner):
        errors = {}

        headquarter_type_id = combiner.get_value_id('headquarter_type')
        subsidiaries = combiner.get_value_to_many('subsidiaries')

        if headquarter_type_id == HeadquarterType.ghq.value.id:
            return {}

        total_subsidiaries = subsidiaries.count() \
            if isinstance(subsidiaries, models.query.QuerySet) else len(subsidiaries)

        if total_subsidiaries > 0:
            message = self.error_messages['global_headquarters_has_subsidiaries']
            errors['headquarter_type'] = message

        return errors

    def _validate_cannot_become_ghq_if_linked_to_another_ghq(self, combiner):
        errors = {}

        headquarter_type_id = combiner.get_value_id('headquarter_type')
        global_headquarters_id = combiner.get_value_id('global_headquarters')

        if (
            headquarter_type_id is not None
            and UUID(headquarter_type_id) == UUID(HeadquarterType.ghq.value.id)
            and global_headquarters_id is not None
        ):
            message = self.error_messages['subsidiary_cannot_be_a_global_headquarters']
            errors['headquarter_type'] = message

        return errors

    def _validate_ghq_is_not_self(self, combiner):
        errors = {}

        pk = combiner.get_value('pk')
        global_headquarters_id = combiner.get_value_id('global_headquarters')

        if (
            pk
            and global_headquarters_id
            and UUID(global_headquarters_id) == pk
        ):
            message = self.error_messages['invalid_global_headquarters']
            errors['global_headquarters'] = message

        return errors

    def _validate_ghq_has_ghq_headquarter_type(self, combiner):
        errors = {}

        global_headquarter = combiner.get_value('global_headquarters')
        if (
            global_headquarter and
            global_headquarter.headquarter_type_id != UUID(HeadquarterType.ghq.value.id)
        ):
            message = self.error_messages['headquarter_type_is_not_global_headquarters']
            errors['global_headquarters'] = message
        return errors

    class Meta:
        model = Company
        fields = (
            'id',
            'reference_code',
            'name',
            'trading_name',
            'uk_based',
            'company_number',
            'vat_number',
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
            'website',
            'trading_address_1',
            'trading_address_2',
            'trading_address_town',
            'trading_address_county',
            'trading_address_postcode',
            'trading_address_country',
            'account_manager',
            'business_type',
            'classification',
            'companies_house_data',
            'contacts',
            'employee_range',
            'export_to_countries',
            'future_interest_countries',
            'headquarter_type',
            'one_list_account_owner',
            'global_headquarters',
            'sector',
            'turnover_range',
            'uk_region',
            'investment_projects_invested_in',
            'investment_projects_invested_in_count',
            'export_experience_category',
        )
        read_only_fields = (
            'archived',
            'archived_documents_url_path',
            'archived_on',
            'archived_reason',
            'reference_code',
        )
        validators = [
            RequiredUnlessAlreadyBlankValidator('sector', 'business_type'),
            RulesBasedValidator(
                ValidationRule(
                    'required',
                    OperatorRule('uk_region', bool),
                    when=EqualsRule('registered_address_country',
                                    Country.united_kingdom.value.id),
                ),
                ValidationRule(
                    'uk_establishment_not_in_uk',
                    EqualsRule('registered_address_country', Country.united_kingdom.value.id),
                    when=EqualsRule('business_type',
                                    BusinessTypeConstant.uk_establishment.value.id),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('company_number', bool),
                    when=EqualsRule('business_type',
                                    BusinessTypeConstant.uk_establishment.value.id),
                ),
                ValidationRule(
                    'invalid_uk_establishment_number_characters',
                    OperatorRule('company_number', has_no_invalid_company_number_characters),
                    when=EqualsRule('business_type',
                                    BusinessTypeConstant.uk_establishment.value.id),
                ),
                ValidationRule(
                    'invalid_uk_establishment_number_prefix',
                    OperatorRule('company_number', has_uk_establishment_number_prefix),
                    when=EqualsRule('business_type',
                                    BusinessTypeConstant.uk_establishment.value.id),
                ),
            ),
            AddressValidator(lazy=True, fields_mapping=Company.TRADING_ADDRESS_VALIDATION_MAPPING),
        ]
        permissions = {
            f'company.{CompanyPermission.read_company_document}': 'archived_documents_url_path',
        }
