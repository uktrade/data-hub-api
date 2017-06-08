from functools import partial

from django.conf import settings

from rest_framework import serializers

from datahub.company.models import (
    Advisor, CompaniesHouseCompany, Company, Contact
)
from datahub.core.serializers import NestedRelatedField
from datahub.interaction.models import Interaction
from datahub.metadata import models as meta_models
from datahub.metadata.serializers import NestedCountrySerializer


class NestedContactSerializer(serializers.ModelSerializer):
    """Nested Contact serializer."""

    class Meta:  # noqa: D101
        model = Contact
        depth = 1
        fields = '__all__'


class NestedInteractionSerializer(serializers.ModelSerializer):
    """Nested Interaction Serializer."""

    class Meta:  # noqa: D101
        model = Interaction
        fields = '__all__'


class CompaniesHouseCompanySerializer(serializers.ModelSerializer):
    """Companies House company serializer."""

    class Meta:  # noqa: D101
        model = CompaniesHouseCompany
        depth = 1
        fields = '__all__'


class AdviserSerializer(serializers.ModelSerializer):
    """Adviser serializer."""

    name = serializers.CharField()

    class Meta:  # noqa: D101
        model = Advisor
        exclude = ('is_staff', 'is_active', 'date_joined', 'password')
        depth = 1


class CompanySerializerReadV1(serializers.ModelSerializer):
    """Company serializer."""

    name = serializers.SerializerMethodField('get_registered_name')
    trading_name = serializers.CharField(source='alias')
    companies_house_data = CompaniesHouseCompanySerializer()
    interactions = NestedInteractionSerializer(many=True)
    contacts = NestedContactSerializer(many=True)
    export_to_countries = NestedCountrySerializer(many=True)
    future_interest_countries = NestedCountrySerializer(many=True)
    uk_based = serializers.BooleanField()
    account_manager = AdviserSerializer()
    registered_address_1 = serializers.SerializerMethodField()
    registered_address_2 = serializers.SerializerMethodField()
    registered_address_3 = serializers.SerializerMethodField()
    registered_address_4 = serializers.SerializerMethodField()
    registered_address_town = serializers.SerializerMethodField()
    registered_address_country = serializers.SerializerMethodField()
    registered_address_county = serializers.SerializerMethodField()
    registered_address_postcode = serializers.SerializerMethodField()

    class Meta:  # noqa: D101
        model = Company
        depth = 1
        fields = '__all__'

    @staticmethod
    def _address_partial(obj, attr):
        """Return the address partial from obj."""
        obj = obj.companies_house_data or obj
        return getattr(obj, attr)

    @staticmethod
    def get_registered_name(obj):
        """Use the CH name, if there's one, else the name."""
        return obj.companies_house_data.name if obj.companies_house_data else obj.name

    def get_registered_address_1(self, obj):
        """Return CH address if present."""
        return self._address_partial(obj, 'registered_address_1')

    def get_registered_address_2(self, obj):
        """Return CH address if present."""
        return self._address_partial(obj, 'registered_address_2')

    def get_registered_address_3(self, obj):
        """Return CH address if present."""
        return self._address_partial(obj, 'registered_address_3')

    def get_registered_address_4(self, obj):
        """Return CH address if present."""
        return self._address_partial(obj, 'registered_address_4')

    @staticmethod
    def get_registered_address_country(obj):
        """Return CH address if present."""
        obj = obj.companies_house_data or obj
        if obj.registered_address_country:
            return {'id': str(obj.registered_address_country.id),
                    'name': obj.registered_address_country.name}
        else:
            return {}

    def get_registered_address_county(self, obj):
        """Return CH address if present."""
        return self._address_partial(obj, 'registered_address_county')

    def get_registered_address_postcode(self, obj):
        """Return CH address if present."""
        return self._address_partial(obj, 'registered_address_postcode')

    def get_registered_address_town(self, obj):
        """Return CH address if present."""
        return self._address_partial(obj, 'registered_address_town')


class CompanySerializerWriteV1(serializers.ModelSerializer):
    """Company serializer for writing operations."""

    classification = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:  # noqa: D101
        model = Company
        fields = '__all__'


NestedAdviserField = partial(
    NestedRelatedField, 'company.Advisor',
    extra_fields=('first_name', 'last_name')
)


class ContactSerializer(serializers.ModelSerializer):
    """Contact serializer for writing operations V3."""

    title = NestedRelatedField(
        meta_models.Title, required=False, allow_null=True
    )
    company = NestedRelatedField(
        Company, required=False, allow_null=True
    )
    adviser = NestedRelatedField(
        Advisor, read_only=True,
        extra_fields=('first_name', 'last_name')
    )
    address_country = NestedRelatedField(
        meta_models.Country, required=False, allow_null=True
    )
    archived = serializers.BooleanField(read_only=True)
    archived_on = serializers.DateTimeField(read_only=True)
    archived_reason = serializers.CharField(read_only=True)
    archived_by = NestedRelatedField(
        settings.AUTH_USER_MODEL, read_only=True,
        extra_fields=('first_name', 'last_name')
    )

    class Meta:  # noqa: D101
        model = Contact
        fields = (
            'id', 'title', 'first_name', 'last_name', 'job_title', 'company', 'adviser',
            'primary', 'telephone_countrycode', 'telephone_number', 'email',
            'address_same_as_company', 'address_1', 'address_2', 'address_3',
            'address_4',
            'address_town', 'address_county', 'address_country',
            'address_postcode',
            'telephone_alternative', 'email_alternative', 'notes',
            'contactable_by_dit',
            'contactable_by_dit_partners', 'contactable_by_email',
            'contactable_by_phone',
            'archived', 'archived_on', 'archived_reason', 'archived_by',
            'created_on'
        )


class _CHPrefferedField(serializers.Field):
    """TODO."""

    def __init__(self, field_name, serializer_field=None, **kwargs):
        """TODO."""
        super().__init__(**kwargs)

        self._serializer_field = serializer_field
        self._field_name = field_name

    def get_attribute(self, instance):
        """TODO."""
        return instance

    def to_internal_value(self, data):
        """TODO."""
        if self._serializer_field:
            return self._serializer_field.to_internal_value(data)
        return data

    def to_representation(self, instance):
        """TODO."""
        field_value = getattr(
            instance.companies_house_data or instance, self._field_name
        )
        if self._serializer_field:
            return self._serializer_field.to_representation(field_value)
        return field_value


class CompanySerializerV3(serializers.ModelSerializer):
    """Company read/write serializer V3."""

    name = _CHPrefferedField('name', required=False, allow_null=True)
    registered_address_1 = _CHPrefferedField(
        'registered_address_1', required=False, allow_null=True
    )
    registered_address_2 = _CHPrefferedField(
        'registered_address_2', required=False, allow_null=True
    )
    registered_address_town = _CHPrefferedField(
        'registered_address_town', required=False, allow_null=True
    )
    registered_address_county = _CHPrefferedField(
        'registered_address_county', required=False, allow_null=True
    )
    registered_address_postcode = _CHPrefferedField(
        'registered_address_postcode', required=False, allow_null=True
    )
    registered_address_country = _CHPrefferedField(
        'registered_address_country', required=False, allow_null=True,
        serializer_field=NestedRelatedField(meta_models.Country)
    )
    trading_name = serializers.CharField(
        source='alias', required=False, allow_null=True
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
    sector = NestedRelatedField(
        meta_models.Sector, required=False, allow_null=True
    )
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

    class Meta:  # noqa: D101
        model = Company
        fields = (
            'id',
            'name',
            'trading_name',
            'uk_based',
            'registered_address_1',
            'registered_address_2',
            'registered_address_3',
            'registered_address_4',
            'registered_address_town',
            'registered_address_county',
            'registered_address_postcode',
            'registered_address_country',
            'created_on',
            'modified_on',
            'archived',
            'archived_on',
            'archived_reason',
            'archived_by',
            'description',
            'website',
            'trading_address_1',
            'trading_address_2',
            'trading_address_3',
            'trading_address_4',
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
            'investment_projects_invested_in_count'
        )
        extra_kwargs = {
            'investment_projects': {'read_only': True},
            'archived': {'read_only': True},
            'archived_on': {'read_only': True},
            'archived_reason': {'read_only': True}
        }


def _get_ch_preffered_field(company_instance, attr_name):
    return getattr(company_instance.companies_house_data or company_instance,
                   attr_name)
