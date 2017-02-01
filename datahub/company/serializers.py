from rest_framework import serializers

from datahub.metadata.serializers import NestedCountrySerializer, NestedTeamSerializer
from .models import Advisor, CompaniesHouseCompany, Company, Contact, Interaction


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


class AdvisorSerializer(serializers.ModelSerializer):
    """Advisor serializer."""

    name = serializers.CharField()

    class Meta:  # noqa: D101
        model = Advisor
        exclude = ('is_staff', 'is_active', 'date_joined')
        depth = 1


class CompanySerializerRead(serializers.ModelSerializer):
    """Company serializer."""

    name = serializers.SerializerMethodField('get_registered_name')
    trading_name = serializers.CharField(source='alias')
    companies_house_data = CompaniesHouseCompanySerializer()
    interactions = NestedInteractionSerializer(many=True)
    contacts = NestedContactSerializer(many=True)
    export_to_countries = NestedCountrySerializer(many=True)
    future_interest_countries = NestedCountrySerializer(many=True)
    uk_based = serializers.BooleanField()
    account_manager = AdvisorSerializer()
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
            return {
                'id': str(obj.registered_address_country.id),
                'name': obj.registered_address_country.name
            }
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


class CompanySerializerWrite(serializers.ModelSerializer):
    """Company serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Company
        fields = '__all__'


class ContactSerializerWrite(serializers.ModelSerializer):
    """Contact serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Contact
        exclude = ('teams',)


class ContactSerializerRead(serializers.ModelSerializer):
    """Contact serializer."""

    teams = NestedTeamSerializer(many=True)
    interactions = NestedInteractionSerializer(many=True)
    name = serializers.CharField()
    address_1 = serializers.SerializerMethodField()
    address_2 = serializers.SerializerMethodField()
    address_3 = serializers.SerializerMethodField()
    address_4 = serializers.SerializerMethodField()
    address_town = serializers.SerializerMethodField()
    address_country = serializers.SerializerMethodField()
    address_county = serializers.SerializerMethodField()
    address_postcode = serializers.SerializerMethodField()

    class Meta:  # noqa: D101
        model = Contact
        depth = 2
        fields = '__all__'

    @staticmethod
    def get_address_1(obj):
        """Handle address."""
        return obj.company.trading_address_1 if obj.address_same_as_company else obj.address_1

    @staticmethod
    def get_address_2(obj):
        """Handle address."""
        return obj.company.trading_address_2 if obj.address_same_as_company else obj.address_2

    @staticmethod
    def get_address_3(obj):
        """Handle address."""
        return obj.company.trading_address_3 if obj.address_same_as_company else obj.address_3

    @staticmethod
    def get_address_4(obj):
        """Handle address."""
        return obj.company.trading_address_4 if obj.address_same_as_company else obj.address_4

    @staticmethod
    def get_address_town(obj):
        """Handle address."""
        return obj.company.trading_address_town if obj.address_same_as_company else obj.address_town

    @staticmethod
    def get_address_country(obj):
        """Handle address."""
        if obj.address_same_as_company:
            if obj.company.trading_address_country:
                return {
                    'id': str(obj.company.trading_address_country.pk),
                    'name': obj.company.trading_address_country.name
                }
            else:
                return {}
        else:
            return {
                'id': str(obj.address_country.pk),
                'name': obj.address_country.name
            } if obj.address_country else {}

    @staticmethod
    def get_address_county(obj):
        """Handle address."""
        return obj.company.trading_address_county if obj.address_same_as_company else obj.address_county

    @staticmethod
    def get_address_postcode(obj):
        """Handle address."""
        return obj.company.trading_address_postcode if obj.address_same_as_company else obj.address_postcode


class InteractionSerializerRead(serializers.ModelSerializer):
    """Interaction Serializer."""

    dit_advisor = AdvisorSerializer()

    class Meta:  # noqa: D101
        model = Interaction
        depth = 2
        fields = '__all__'


class InteractionSerializerWrite(serializers.ModelSerializer):
    """Interaction Serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Interaction
        fields = '__all__'
