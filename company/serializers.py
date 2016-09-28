from rest_framework import serializers

from .models import Company, CompaniesHouseCompany, Contact, Interaction


class CompaniesHouseCompanySerializer(serializers.ModelSerializer):
    """Companies House company serializer."""

    class Meta:
        model = CompaniesHouseCompany
        depth = 1


class CompanySerializer(serializers.ModelSerializer):
    """Company serializer.

    Extends CDMS data with Company House data
    """
    id = serializers.CharField(required=False)
    companies_house_data = CompaniesHouseCompanySerializer(read_only=True)

    class Meta:
        model = Company
        depth = 1


class ContactSerializer(serializers.ModelSerializer):
    """Contact serializer."""

    class Meta:
        model = Contact
        depth = 2


class InteractionSerializer(serializers.ModelSerializer):
    """Interaction Serializer."""

    class Meta:
        model = Interaction
        depth = 2
