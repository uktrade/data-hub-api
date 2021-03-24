from collections import Counter
from functools import partial
from operator import not_
from uuid import UUID

from django.conf import settings
from django.db import models, transaction
from django.utils.timezone import now
from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.company import consent
from datahub.company.constants import (
    BusinessTypeConstant,
    OneListTierID,
)
from datahub.company.models import (
    Advisor,
    Company,
    CompanyExportCountry,
    CompanyPermission,
    Contact,
    ContactPermission,
    ExportExperienceCategory,
    OneListCoreTeamMember,
    OneListTier,
)
from datahub.company.tasks import update_contact_consent
from datahub.company.validators import (
    has_no_invalid_company_number_characters,
    has_uk_establishment_number_prefix,
)
from datahub.core.api_client import get_zipkin_headers
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

NestedAdviserWithEmailAndTeamField = partial(
    NestedRelatedField,
    'company.Advisor',
    extra_fields=(
        'name',
        'contact_email',
        ('dit_team', NestedRelatedField('metadata.Team')),
    ),
)

# like NestedAdviserField but includes dit_team with uk_region and country
NestedAdviserWithEmailAndTeamGeographyField = partial(
    NestedRelatedField,
    'company.Advisor',
    extra_fields=(
        'name',
        'first_name',
        'last_name',
        'contact_email',
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


class ContactSerializer(PermittedFieldsModelSerializer):
    """Contact serializer for writing operations V3."""

    default_error_messages = {
        'address_same_as_company_and_has_address': gettext_lazy(
            'Please select either address_same_as_company or enter an address manually, not both!',
        ),
        'no_address': gettext_lazy(
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


class ConsentMarketingField(serializers.BooleanField):
    """
    ConsentMarketingField will lookup consent data.
    The model that this fields is used must have an email field
    BooleanField is subclassed here for validation.
    """

    def to_internal_value(self, data):
        """Validate boolean on incoming data."""
        return {
            'accepts_dit_email_marketing': super().to_internal_value(data),
        }

    def to_representation(self, value):
        """Lookup from consent service api/"""
        try:
            representation = consent.get_one(value.email)
        except consent.ConsentAPIException:
            representation = False
        return representation


class ContactDetailSerializer(ContactSerializer):
    """
    This is the same as the ContactSerializer except it includes
    accepts_dit_email_marketing in the fields. Only 3 endpoints will use this serialiser
    """

    accepts_dit_email_marketing = ConsentMarketingField(source='*', required=False)

    class Meta(ContactSerializer.Meta):
        fields = ContactSerializer.Meta.fields + ('accepts_dit_email_marketing',)

    def _notify_consent_service(self, validated_data):
        """
        Trigger the update_contact_consent task with the current version
        of `validated_data`. The actual enqueuing of the task happens in the
        on_commit hook so it won't actually notify the consent service unless
        the database transaction was successful.
        """
        if 'accepts_dit_email_marketing' not in validated_data:
            # If no consent value in request body
            return
        # Remove the accepts_dit_email_marketing from validated_data
        accepts_dit_email_marketing = validated_data.pop('accepts_dit_email_marketing')
        # If consent value in POST, notify
        combiner = DataCombiner(self.instance, validated_data)
        request = self.context.get('request', None)
        transaction.on_commit(
            lambda: update_contact_consent.apply_async(
                args=(
                    combiner.get_value('email'),
                    accepts_dit_email_marketing,
                ),
                kwargs={
                    'modified_at': now().isoformat(),
                    'zipkin_headers': get_zipkin_headers(request),
                },
            ),
        )

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new instance using this serializer

        :return: created instance
        """
        self._notify_consent_service(validated_data)
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update the given instance with validated_data

        :return: updated instance
        """
        self._notify_consent_service(validated_data)
        return super().update(instance, validated_data)


class CompanyExportCountrySerializer(serializers.ModelSerializer):
    """
    Export country serializer holding `Country` and its status.
    """

    country = NestedRelatedField(meta_models.Country)

    class Meta:
        model = CompanyExportCountry
        fields = ('country', 'status')


class CompanySerializer(PermittedFieldsModelSerializer):
    """
    Base Company read/write serializer
    Note that there is special validation for company number for UK establishments. This is
    because we don't get UK establishments in our Companies House data file at present, so users
    have to enter company numbers for UK establishments manually.
    """

    default_error_messages = {
        'invalid_uk_establishment_number_prefix': gettext_lazy(
            'This must be a valid UK establishment number, beginning with BR.',
        ),
        'invalid_uk_establishment_number_characters': gettext_lazy(
            'This field can only contain the letters A to Z and numbers (no symbols, punctuation '
            'or spaces).',
        ),
        'global_headquarters_hq_type_is_not_global_headquarters': gettext_lazy(
            'Company to be linked as global headquarters must be a global headquarters.',
        ),
        'invalid_global_headquarters': gettext_lazy(
            'Global headquarters cannot point to itself.',
        ),
        'global_headquarters_has_subsidiaries': gettext_lazy(
            'Subsidiaries have to be unlinked before changing headquarter type.',
        ),
        'subsidiary_cannot_be_a_global_headquarters': gettext_lazy(
            'A company cannot both be and have a global headquarters.',
        ),
        'uk_establishment_not_in_uk': gettext_lazy(
            'A UK establishment (branch of non-UK company) must be in the UK.',
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
        meta_models.Country, many=True, read_only=True,
    )
    future_interest_countries = NestedRelatedField(
        meta_models.Country, many=True, read_only=True,
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
    registered_address = AddressSerializer(
        source_model=Company,
        address_source_prefix='registered_address',
        required=False,
        allow_null=True,
    )
    address = AddressSerializer(source_model=Company, address_source_prefix='address')
    export_countries = CompanyExportCountrySerializer(many=True, read_only=True)

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

        combiner = DataCombiner(self.instance, data)

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

        field = NestedAdviserWithEmailAndTeamGeographyField()
        return field.to_representation(global_account_manager)

    def create(self, validated_data):
        """
        Override create method to ensure that all Company objects created through this serializer
        have pending_dnb_investigation=True. This ensures that we always mark Company records based
        on untrusted data in a consistent way.
        """
        if not validated_data.get('duns_number'):
            validated_data['pending_dnb_investigation'] = True
        return Company.objects.create(**validated_data)

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
            'address',
            'registered_address',
            'pending_dnb_investigation',
            'export_potential',
            'great_profile_status',
            'is_global_ultimate',
            'global_ultimate_duns_number',
            'dnb_modified_on',
            'export_countries',
            'export_segment',
            'export_sub_segment',
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
            'pending_dnb_investigation',
            'export_potential',
            'great_profile_status',
            'is_global_ultimate',
            'global_ultimate_duns_number',
            'dnb_modified_on',
            'export_countries',
        )
        dnb_read_only_fields = (
            'name',
            'trading_names',
            'company_number',
            'vat_number',
            'business_type',
            'employee_range',
            'turnover_range',
            'address',
            'registered_address',
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
        permissions = {
            f'company.{CompanyPermission.view_company_document}': 'archived_documents_url_path',
            'company.view_companyexportcountry': 'export_countries',
        }


class AssignRegionalAccountManagerSerializer(serializers.Serializer):
    """
    Serialiser for assigning an international trade adviser as the account manager of a
    company.
    """

    target_one_list_tier_id = OneListTierID.tier_d_international_trade_advisers.value
    default_error_messages = {
        'cannot_change_account_manager_of_one_list_subsidiary':
            gettext_lazy("A lead adviser can't be set on a subsidiary of a One List company."),
        'cannot_change_account_manager_for_other_one_list_tiers':
            gettext_lazy("A lead adviser can't be set for companies on this One List tier."),
    }
    regional_account_manager = NestedRelatedField(Advisor)

    def validate(self, attrs):
        """Validate that the change of One List account manager and tier is allowed."""
        attrs = super().validate(attrs)
        global_headquarters = self.instance.global_headquarters

        if global_headquarters and global_headquarters.one_list_tier_id:
            raise serializers.ValidationError(
                self.error_messages['cannot_change_account_manager_of_one_list_subsidiary'],
                code='cannot_change_account_manager_of_one_list_subsidiary',
            )

        if self.instance.one_list_tier_id not in (None, self.target_one_list_tier_id):
            raise serializers.ValidationError(
                self.error_messages['cannot_change_account_manager_for_other_one_list_tiers'],
                code='cannot_change_account_manager_for_other_one_list_tiers',
            )

        return attrs

    def save(self, adviser):
        """Update the company's One List account manager and tier."""
        self.instance.assign_one_list_account_manager_and_tier(
            self.validated_data['regional_account_manager'],
            self.target_one_list_tier_id,
            adviser,
        )
        return self.instance


class SelfAssignAccountManagerSerializer(serializers.Serializer):
    """
    Serialiser for assigning an international trade adviser as the account manager of a
    company.
    """

    target_one_list_tier_id = OneListTierID.tier_d_international_trade_advisers.value
    default_error_messages = {
        'cannot_change_account_manager_of_one_list_subsidiary':
            gettext_lazy("A lead adviser can't be set on a subsidiary of a One List company."),
        'cannot_change_account_manager_for_other_one_list_tiers':
            gettext_lazy("A lead adviser can't be set for companies on this One List tier."),
    }

    def validate(self, attrs):
        """Validate that the change of One List account manager and tier is allowed."""
        attrs = super().validate(attrs)
        global_headquarters = self.instance.global_headquarters

        if global_headquarters and global_headquarters.one_list_tier_id:
            raise serializers.ValidationError(
                self.error_messages['cannot_change_account_manager_of_one_list_subsidiary'],
                code='cannot_change_account_manager_of_one_list_subsidiary',
            )

        if self.instance.one_list_tier_id not in (None, self.target_one_list_tier_id):
            raise serializers.ValidationError(
                self.error_messages['cannot_change_account_manager_for_other_one_list_tiers'],
                code='cannot_change_account_manager_for_other_one_list_tiers',
            )

        return attrs

    def save(self, adviser):
        """Update the company's One List account manager and tier."""
        self.instance.assign_one_list_account_manager_and_tier(
            adviser,
            self.target_one_list_tier_id,
            adviser,
        )
        return self.instance


class _RemoveCompanyFromOneListSerializer(serializers.Serializer):
    """
    Serialiser for removing company from One list.
    """

    def save(self, by):
        """Unset the company's One List account manager and tier."""
        self.instance.remove_from_one_list(by)
        return self.instance


class RemoveAccountManagerSerializer(_RemoveCompanyFromOneListSerializer):
    """
    Serialiser for removing an international trade adviser as the account manager of a
    company.
    """

    allowed_one_list_tier_id = OneListTierID.tier_d_international_trade_advisers.value
    default_error_messages = {
        'cannot_change_account_manager_for_other_one_list_tiers':
            gettext_lazy("A lead adviser can't be removed from companies on this One List tier."),
    }

    def validate(self, attrs):
        """Validate that the change of One List account manager and tier is allowed."""
        attrs = super().validate(attrs)

        if self.instance.one_list_tier_id not in (None, self.allowed_one_list_tier_id):
            raise serializers.ValidationError(
                self.error_messages['cannot_change_account_manager_for_other_one_list_tiers'],
                code='cannot_change_account_manager_for_other_one_list_tiers',
            )

        return attrs


class RemoveCompanyFromOneListSerializer(_RemoveCompanyFromOneListSerializer):
    """Serialiser for removing company from One List."""

    excluded_one_list_tier_id = OneListTierID.tier_d_international_trade_advisers.value
    default_error_messages = {
        'cannot_remove_lead_ita':
            gettext_lazy(
                'It`s not possible to remove a lead ITA from a company using'
                'One List admin functionality',
            ),
    }

    def validate(self, attrs):
        """Validate that the change of One List account manager and tier is allowed."""
        attrs = super().validate(attrs)

        if self.instance.one_list_tier_id == self.excluded_one_list_tier_id:
            raise serializers.ValidationError(
                self.error_messages['cannot_remove_lead_ita'],
                code='cannot_remove_lead_ita',
            )

        return attrs


class AssignOneListTierAndGlobalAccountManagerSerializer(serializers.Serializer):
    """
    Serializer for assigning One List tier and global account manager to a company.
    """

    excluded_one_list_tier_id = OneListTierID.tier_d_international_trade_advisers.value

    default_error_messages = {
        'cannot_assign_subsidiary_to_one_list':
            gettext_lazy('A subsidiary cannot be on One List.'),
        'cannot_assign_company_one_list_tier':
            gettext_lazy('A company can only have this One List tier assigned by ITA.'),
        'cannot_change_company_with_current_one_list_tier':
            gettext_lazy('A company on this One List tier can only be changed by ITA.'),
    }

    one_list_tier = NestedRelatedField(OneListTier)
    global_account_manager = NestedRelatedField(Advisor)

    def validate_one_list_tier(self, one_list_tier):
        """Validates new One List tier."""
        if one_list_tier and one_list_tier.id == self.excluded_one_list_tier_id:
            raise serializers.ValidationError(
                self.error_messages['cannot_assign_company_one_list_tier'],
                code='cannot_assign_company_one_list_tier',
            )
        return one_list_tier

    def validate(self, attrs):
        """
        Validate that given one list tier and global account manager can be assigned to a company.
        """
        attrs = super().validate(attrs)

        if self.instance.global_headquarters:
            raise serializers.ValidationError(
                self.error_messages['cannot_assign_subsidiary_to_one_list'],
                code='cannot_assign_subsidiary_to_one_list',
            )

        old_one_list_tier = self.instance.one_list_tier
        if old_one_list_tier and old_one_list_tier.id == self.excluded_one_list_tier_id:
            raise serializers.ValidationError(
                self.error_messages['cannot_change_company_with_current_one_list_tier'],
                code='cannot_change_company_with_current_one_list_tier',
            )

        return attrs

    def save(self, adviser):
        """Update company One List account manager and tier."""
        self.instance.assign_one_list_account_manager_and_tier(
            self.validated_data['global_account_manager'],
            self.validated_data['one_list_tier'].id,
            adviser,
        )
        return self.instance


class UpdateExportDetailsSerializer(serializers.Serializer):
    """
    Serializer for updating export related information of a company.
    For now this updates export countries along with repective status.
    """

    default_error_messages = {
        'duplicate_export_country': gettext_lazy(
            'You cannot enter the same country in multiple fields.',
        ),
    }

    export_countries = CompanyExportCountrySerializer(many=True, required=True)

    def validate(self, data):
        """
        Validate export countries.
        Updating export countries is not valid when feature flag is ON.
        And same country can't be added twice.
        """
        data = super().validate(data)

        # check for duplicate countries
        export_countries = data.get('export_countries', [])
        countries = [item['country'] for item in export_countries]
        if len(countries) > len(set(countries)):
            raise serializers.ValidationError(self.error_messages['duplicate_export_country'])

        return data

    @transaction.atomic
    def save(self, adviser):
        """Save it"""
        export_countries = self.validated_data.pop('export_countries', [])
        self._update_export_countries_model(self.instance, export_countries, adviser)

    def _update_export_countries_model(self, company, validated_export_countries, adviser):
        """
        Adds/updates export countries related to a company within validated_export_countries.
        And removes existing ones that are not in the list.
        """
        for item in validated_export_countries:
            country = meta_models.Country.objects.get(id=item['country'].id)
            status = item['status']
            company.add_export_country(
                country=country,
                status=status,
                record_date=company.modified_on,
                adviser=adviser,
                track_history=True,
            )

        existing_country_ids = [item.country.id for item in company.export_countries.all()]
        new_country_ids = [item['country'].id for item in validated_export_countries]
        country_ids_delta = list(set(existing_country_ids) - set(new_country_ids))

        for country_id in country_ids_delta:
            company.delete_export_country(country_id, adviser)

        self._sync_to_company_export_country_fields(company, adviser)

    def _sync_to_company_export_country_fields(self, company, adviser):
        """
        Helper function to sync data from `ComapnyExportCountry` model back
        into `Company` export country fields: `exporting_to_countries` and
        `future_interest_countries`.
        """
        currently_exporting_items = CompanyExportCountry.objects.filter(
            company=company,
            status=CompanyExportCountry.Status.CURRENTLY_EXPORTING,
        )
        exporting_to_countries = [item.country for item in currently_exporting_items]

        future_interest_items = CompanyExportCountry.objects.filter(
            company=company,
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
        )
        future_interest_countries = [item.country for item in future_interest_items]

        company.export_to_countries.set(exporting_to_countries)
        company.future_interest_countries.set(future_interest_countries)
        company.modified_by = adviser
        company.save()


class PublicCompanySerializer(CompanySerializer):
    """
    Read-only serialiser for the Hawk-authenticated company view.

    This is a slightly stripped down read-only version of the v4 company serialiser. Some fields
    containing personal data are deliberately omitted.
    """

    class Meta(CompanySerializer.Meta):
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
            'export_segment',
            'export_sub_segment',
        )
        permissions = {}
        read_only_fields = fields


class AdviserListSerializer(serializers.ListSerializer):
    """Adviser list serialiser that adds validation for duplicates."""

    default_error_messages = {
        'duplicate_adviser': gettext_lazy(
            'You cannot add the same adviser more than once.',
        ),
    }

    def run_validation(self, data=serializers.empty):
        """
        Validates that there are no duplicate advisers.

        Unfortunately, overriding validate() results in a error dict being returned and the errors
        being placed in non_field_errors. Hence, run_validation() is overridden instead (to get
        the expected behaviour of an error list being returned, with each entry corresponding
        to each item in the request body).
        """
        value = super().run_validation(data)
        counts = Counter(adviser['adviser'] for adviser in value)

        if len(counts) == len(value):
            return value

        errors = []
        for item in value:
            item_errors = {}

            if counts[item['adviser']] > 1:
                item_errors['adviser'] = [self.error_messages['duplicate_adviser']]

            errors.append(item_errors)

        raise serializers.ValidationError(errors)


class UniqueAdvisersBaseSerializer(serializers.ModelSerializer):
    """Base serialiser to use with models holding advisers."""

    adviser = NestedAdviserField()

    @classmethod
    def many_init(cls, *args, **kwargs):
        """Initialises a many=True instance of the serialiser with a custom list serialiser."""
        child = cls(context=kwargs.get('context'))
        return AdviserListSerializer(child=child, *args, **kwargs)

    class Meta:
        # Explicitly set validator as extra protection against a unique together validator being
        # added.
        # (UniqueTogetherValidator would not function correctly when multiple items are being
        # updated at once.)
        validators = []


class OneListCoreTeamMemberModelSerializer(UniqueAdvisersBaseSerializer):
    """One List Core Team Member model serializer."""

    adviser = NestedAdviserField()
    company = NestedRelatedField(Company, read_only=True)

    class Meta(UniqueAdvisersBaseSerializer.Meta):
        model = OneListCoreTeamMember
        fields = ('adviser', 'company')


class UpdateOneListCoreTeamMembersSerializer(serializers.Serializer):
    """
    One List Core Team Members update serialier.

    This serialiser is being used by the core team update view.
    """

    core_team_members = OneListCoreTeamMemberModelSerializer(many=True)

    @transaction.atomic
    def save(self, adviser):
        """Save it"""
        core_team_members = self.validated_data.pop('core_team_members', [])
        self._update_core_team_members(self.instance, core_team_members, adviser)

    def _update_core_team_members(self, company, validated_core_team_members, adviser):
        """
        Adds/updates core team members of a company within validated_core_team_members.
        And removes existing ones that are not in the list.
        """
        for item in validated_core_team_members:
            company.add_one_list_core_team_member(item['adviser'])

        existing_adviser_ids = [
            item.adviser.id for item in company.one_list_core_team_members.all()
        ]
        new_core_team_member_ids = [item['adviser'].id for item in validated_core_team_members]
        existing_adviser_ids_delta = list(
            set(existing_adviser_ids) - set(new_core_team_member_ids),
        )

        for adviser_id in existing_adviser_ids_delta:
            company.delete_one_list_core_team_member(adviser_id)


class OneListCoreTeamMemberSerializer(serializers.Serializer):
    """One List Core Team Member Serializer."""

    adviser = NestedAdviserWithEmailAndTeamGeographyField()
    is_global_account_manager = serializers.BooleanField()
