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

    @staticmethod
    def get_registered_name(obj):
        """Use the CH name, if there's one, else the name."""
        return obj.companies_house_data.name if obj.companies_house_data else obj.name


class CompanySerializerWrite(serializers.ModelSerializer):
    """Company serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Company


class ContactSerializerWrite(serializers.ModelSerializer):
    """Contact serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Contact


class ContactSerializerRead(serializers.ModelSerializer):
    """Contact serializer."""

    teams = NestedTeamSerializer(many=True)
    interactions = NestedInteractionSerializer(many=True)
    name = serializers.CharField()

    class Meta:  # noqa: D101
        model = Contact
        depth = 2


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
