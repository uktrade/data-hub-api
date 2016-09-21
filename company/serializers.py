from rest_framework import serializers

from .models import Company, Contact, Interaction


class CompanySerializer(serializers.ModelSerializer):
    """Company serializer.

    Extends CDMS data with Company House data
    """

    class Meta:
        model = Company


class ContactSerializer(serializers.ModelSerializer):
    """Contact serializer."""

    class Meta:
        model = Contact


class InteractionSerializer(serializers.ModelSerializer):
    """Interaction Serializer."""

    class Meta:
        model = Interaction
