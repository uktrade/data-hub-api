from rest_framework import serializers

from .models import Advisor, CompaniesHouseCompany, Company, Contact, Country, Interaction, Team


class NestedContactSerializer(serializers.ModelSerializer):
    """Nested Contact serializer."""

    class Meta:  # noqa: D101
        model = Contact
        depth = 1


class NestedCountrySerializer(serializers.ModelSerializer):
    """Nested Country serializer."""

    class Meta:  # noqa: D101
        model = Country


class NestedInteractionSerializer(serializers.ModelSerializer):
    """Nested Interaction Serializer."""

    class Meta:  # noqa: D101
        model = Interaction


class NestedTeamSerializer(serializers.ModelSerializer):
    """Nested Team serializer."""

    class Meta:  # noqa: D101
        model = Team


class CompaniesHouseCompanySerializer(serializers.ModelSerializer):
    """Companies House company serializer."""

    class Meta:  # noqa: D101
        model = CompaniesHouseCompany
        depth = 1


class AdvisorSerializer(serializers.ModelSerializer):
    """Advisor serializer."""

    name = serializers.CharField()

    class Meta:  # noqa: D101
        model = Advisor
        exclude = ('username', 'is_staff', 'is_active', 'date_joined')
        depth = 1


class CompanySerializerRead(serializers.ModelSerializer):
    """Company serializer."""

    name = serializers.SerializerMethodField('get_registered_name')
    trading_name = serializers.CharField(source='alias')
    registered_address = serializers.SerializerMethodField()
    trading_address = serializers.SerializerMethodField()
    companies_house_data = CompaniesHouseCompanySerializer()
    interactions = NestedInteractionSerializer(many=True)
    contacts = NestedContactSerializer(many=True)
    export_to_countries = NestedCountrySerializer(many=True)
    future_interest_countries = NestedCountrySerializer(many=True)
    uk_based = serializers.BooleanField()
    account_manager = AdvisorSerializer()

    class Meta:  # noqa: D101
        model = Company
        depth = 1
        # we present the addresses as nested objects
        exclude = (
            'registered_address_1',
            'registered_address_2',
            'registered_address_3',
            'registered_address_4',
            'registered_address_town',
            'registered_address_country',
            'registered_address_county',
            'registered_address_postcode',
            'trading_address_1',
            'trading_address_2',
            'trading_address_3',
            'trading_address_4',
            'trading_address_town',
            'trading_address_country',
            'trading_address_county',
            'trading_address_postcode',
        )

    @staticmethod
    def get_registered_name(obj):
        """Use the CH name, if there's one, else the name."""
        return obj.companies_house_data.name if obj.companies_house_data else obj.name

    @staticmethod
    def get_registered_address(obj):
        """Use CH address, if there's one, else the registered address."""
        obj = obj.companies_house_data or obj
        return {
            'address_1': obj.registered_address_1,
            'address_2': obj.registered_address_2,
            'address_3': obj.registered_address_3,
            'address_4': obj.registered_address_4,
            'address_town': obj.registered_address_town,
            'address_country': {
                'id': str(obj.registered_address_country.pk),
                'name': obj.registered_address_country.name
            },
            'address_county': obj.registered_address_county,
            'address_postcode': obj.registered_address_postcode,
        }

    @staticmethod
    def get_trading_address(obj):
        """Trading address exists in Leeloo only."""
        if obj.trading_address_country:
            return {
                'address_1': obj.trading_address_1,
                'address_2': obj.trading_address_2,
                'address_3': obj.trading_address_3,
                'address_4': obj.trading_address_4,
                'address_town': obj.trading_address_town,
                'address_country': {
                    'id': str(obj.trading_address_country.pk),
                    'name': obj.trading_address_country.name
                },
                'address_county': obj.trading_address_county,
                'address_postcode': obj.trading_address_postcode,
            }
        else:
            return {}


class CompanySerializerWrite(serializers.ModelSerializer):
    """Company serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Company


class ContactSerializerWrite(serializers.ModelSerializer):
    """Contact serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Contact
        exclude = ('teams',)


class ContactSerializerRead(serializers.ModelSerializer):
    """Contact serializer."""

    teams = NestedTeamSerializer(many=True)
    interactions = NestedInteractionSerializer(many=True)
    address = serializers.DictField()
    name = serializers.CharField()

    class Meta:  # noqa: D101
        model = Contact
        depth = 2
        # we present the addresses as nested objects
        exclude = (
            'address_1',
            'address_2',
            'address_3',
            'address_4',
            'address_town',
            'address_country',
            'address_county',
            'address_postcode',
        )


class InteractionSerializerRead(serializers.ModelSerializer):
    """Interaction Serializer."""

    dit_advisor = AdvisorSerializer()

    class Meta:  # noqa: D101
        model = Interaction
        depth = 2


class InteractionSerializerWrite(serializers.ModelSerializer):
    """Interaction Serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Interaction
