from functools import partial

from django.conf import settings

from rest_framework import fields, serializers

from datahub.company.models import (
    Advisor, CompaniesHouseCompany, Company, Contact
)
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import RequiredUnlessAlreadyBlank
from datahub.interaction.models import Interaction
from datahub.metadata import models as meta_models
from datahub.metadata.serializers import NestedCountrySerializer


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class AdviserSerializer(serializers.ModelSerializer):
    """Adviser serializer."""

    name = serializers.CharField()

    class Meta:  # noqa: D101
        model = Advisor
        fields = ('id', 'name', 'last_login', 'first_name', 'last_name', 'email', 'dit_team')
        depth = 1


class NestedContactSerializer(serializers.ModelSerializer):
    """Nested Contact serializer."""

    adviser = AdviserSerializer()

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
        extra_kwargs = {
            'registered_address_country': {'required': True, 'allow_null': False},
        }
        validators = [RequiredUnlessAlreadyBlank('sector')]


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
    primary = serializers.BooleanField()

    class Meta:  # noqa: D101
        model = Contact
        fields = (
            'id',
            'title',
            'first_name',
            'last_name',
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
            'contactable_by_dit_partners',
            'contactable_by_email',
            'contactable_by_phone',
            'archived',
            'archived_on',
            'archived_reason',
            'archived_by',
            'created_on'
        )


class _CHPreferredField(serializers.Field):
    """Serializer field that returns values from Companies House data in
    preference to the the model instance itself.

    The serializer field works by acting as a proxy to another serializer
    field. Writes still occur directly to the model (and not to the
    Companies House data).
    """

    def __init__(self, field_class=None, **kwargs):
        """Initialises the field, and creates the underlying field."""
        super().__init__()
        self._serializer_field = field_class(**kwargs)

    def bind(self, field_name, parent):
        """Sets the field name and parent."""
        super().bind(field_name, parent)
        self._serializer_field.bind(field_name, parent)

    def run_validation(self, data=fields.empty):
        """Validates user-provided data, returning the deserialized value."""
        return self._serializer_field.run_validation(data)

    def get_value(self, dictionary):
        """Gets the value for this field from serialized data."""
        return self._serializer_field.get_value(dictionary)

    def get_attribute(self, instance):
        """Gets the value from this field from a model instance.

        This is used in the serialized representation. Data from Companies
        House is used if Companies House data is present.
        """
        used_instance = instance.companies_house_data or instance
        return self._serializer_field.get_attribute(used_instance)

    def to_internal_value(self, data):
        """Deserializes the a user-provided value."""
        return self._serializer_field.to_internal_value(data)

    def to_representation(self, value):
        """Returns the serialized representation of this value."""
        return self._serializer_field.to_representation(value)


class CompanySerializerV3(serializers.ModelSerializer):
    """Company read/write serializer V3."""

    name = _CHPreferredField(
        max_length=MAX_LENGTH, allow_blank=True, field_class=serializers.CharField
    )
    registered_address_1 = _CHPreferredField(
        max_length=MAX_LENGTH, field_class=serializers.CharField
    )
    registered_address_2 = _CHPreferredField(
        required=False, allow_null=True, max_length=MAX_LENGTH,
        allow_blank=True, field_class=serializers.CharField
    )
    registered_address_town = _CHPreferredField(
        max_length=MAX_LENGTH, field_class=serializers.CharField
    )
    registered_address_county = _CHPreferredField(
        required=False, allow_null=True, max_length=MAX_LENGTH,
        allow_blank=True, field_class=serializers.CharField
    )
    registered_address_postcode = _CHPreferredField(
        required=False, allow_null=True, max_length=MAX_LENGTH,
        allow_blank=True, field_class=serializers.CharField
    )
    registered_address_country = _CHPreferredField(
        model=meta_models.Country, field_class=NestedRelatedField
    )
    trading_name = serializers.CharField(
        source='alias', required=False, allow_null=True, allow_blank=True
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

    class Meta:  # noqa: D101
        model = Company
        fields = (
            'id',
            'name',
            'trading_name',
            'uk_based',
            'company_number',
            'registered_address_1',
            'registered_address_2',
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
            'archived': {'read_only': True},
            'archived_on': {'read_only': True},
            'archived_reason': {'read_only': True}
        }
        validators = [RequiredUnlessAlreadyBlank('sector')]
