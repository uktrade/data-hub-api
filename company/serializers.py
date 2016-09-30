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

    companies_house_data = CompaniesHouseCompanySerializer(read_only=True)
    interactions = NestedInteractionSerializer(many=True, read_only=True)
    contacts = NestedContactSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        depth = 1


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
