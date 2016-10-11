from rest_framework import serializers

from .models import Company, CompaniesHouseCompany, Contact, Interaction


class NestedContactSerializer(serializers.ModelSerializer):
    """Nested Contact serializer."""

    class Meta:
        model = Contact


class NestedInteractionSerializer(serializers.ModelSerializer):
    """Nested Interaction Serializer."""

    class Meta:
        model = Interaction


class CompaniesHouseCompanySerializer(serializers.ModelSerializer):
    """Companies House company serializer."""

    class Meta:
        model = CompaniesHouseCompany
        depth = 1


class CompanySerializerRead(serializers.ModelSerializer):
    """Company serializer."""

    registered_name = serializers.SerializerMethodField()
    registered_address = serializers.SerializerMethodField()
    trading_address = serializers.SerializerMethodField()
    companies_house_data = CompaniesHouseCompanySerializer(read_only=True)
    interactions = NestedInteractionSerializer(many=True, read_only=True)
    contacts = NestedContactSerializer(many=True, read_only=True)

    @staticmethod
    def _format_address(obj):
        return {
            'registered_address_1': obj.registered_address_1,
            'registered_address_2': obj.registered_address_2,
            'registered_address_3': obj.registered_address_3,
            'registered_address_4': obj.registered_address_4,
            'registered_address_town': obj.registered_address_town,
            'registered_address_country': obj.registered_address_country.name,
            'registered_address_county': obj.registered_address_county,
            'registered_address_postcode': obj.registered_address_postcode,
        }

    @staticmethod
    def get_registered_name(obj):
        """Use the CH name, if there's one, else the name."""
        return obj.companies_house_data.name if obj.companies_house_data else obj.name

    def get_registered_address(self, obj):
        """Use CH address, if there's one, else the registered address."""
        obj = obj.companies_house_data or obj
        return self._format_address(obj)

    def get_trading_address(self, obj):
        """Trading address exists in Leeloo only."""
        return self._format_address(obj)

    class Meta:
        model = Company
        depth = 1
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


class CompanySerializerWrite(serializers.ModelSerializer):
    """Company serializer for writing operations."""

    class Meta:
        model = Company


class ContactSerializerWrite(serializers.ModelSerializer):
    """Contact serializer for writing operations."""

    class Meta:
        model = Contact


class ContactSerializerRead(serializers.ModelSerializer):
    """Contact serializer."""

    class Meta:
        model = Contact
        depth = 2


class InteractionSerializerRead(serializers.ModelSerializer):
    """Interaction Serializer."""

    class Meta:
        model = Interaction
        depth = 2


class InteractionSerializerWrite(serializers.ModelSerializer):
    """Interaction Serializer for writing operations."""

    class Meta:
        model = Interaction
