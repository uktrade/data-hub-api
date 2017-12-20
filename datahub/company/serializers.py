from functools import partial

from django.conf import settings
from django.db import models
from rest_framework import serializers

from datahub.company.models import (
    Advisor, CompaniesHouseCompany, Company, CompanyPermission,
    Contact, ContactPermission, ExportExperienceCategory,
)
from datahub.core.serializers import NestedRelatedField, RelaxedURLField
from datahub.core.validators import RequiredUnlessAlreadyBlankValidator
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


class CompaniesHouseCompanySerializer(serializers.ModelSerializer):
    """Companies House company serializer."""

    class Meta:
        model = CompaniesHouseCompany
        depth = 1
        fields = '__all__'


NestedAdviserField = partial(
    NestedRelatedField, 'company.Advisor',
    extra_fields=('first_name', 'last_name', 'name')
)


class ContactSerializer(serializers.ModelSerializer):
    """Contact serializer for writing operations V3."""

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

    def __init__(self, *args, **kwargs):
        """Initialise Contact serialiser and check permissions."""
        super().__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context and 'request' in context:
            request = context['request']
            permission = f'company.{ContactPermission.read_contact_document}'
            if not request.user.has_perm(permission):
                self.fields.pop('archived_documents_url_path')


class CompanySerializer(serializers.ModelSerializer):
    """Company read/write serializer V3."""

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
    children = NestedRelatedField('company.Company', many=True, required=False)
    classification = NestedRelatedField(
        meta_models.CompanyClassification, required=False, allow_null=True
    )
    companies_house_data = CompaniesHouseCompanySerializer(read_only=True)
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
    parent = NestedRelatedField(
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
            'children',
            'classification',
            'companies_house_data',
            'contacts',
            'employee_range',
            'export_to_countries',
            'future_interest_countries',
            'headquarter_type',
            'one_list_account_owner',
            'parent',
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
        validators = [RequiredUnlessAlreadyBlankValidator('sector', 'business_type')]

    def __init__(self, *args, **kwargs):
        """Initialise Company serialiser and check permissions."""
        super().__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context and 'request' in context:
            request = context['request']
            permission = f'company.{CompanyPermission.read_company_document}'
            if not request.user.has_perm(permission):
                self.fields.pop('archived_documents_url_path')
