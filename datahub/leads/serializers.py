from django.conf import settings
from rest_framework import serializers

from datahub.company.models import Advisor, Company, Contact
from datahub.core.serializers import NestedRelatedField
from datahub.metadata import models as meta_models


class BusinessLeadSerializer(serializers.ModelSerializer):
    """Business lead serialiser."""

    company = NestedRelatedField(
        Company, required=False, allow_null=True
    )
    advisor = NestedRelatedField(
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
            'id', 'first_name', 'last_name', 'job_title', 'company_name',
            'company', 'advisor', 'telephone_number', 'email',
            'address_1', 'address_2', 'address_town', 'address_county',
            'address_country', 'address_postcode', 'telephone_alternative',
            'email_alternative', 'contactable_by_dit',
            'contactable_by_dit_partners', 'contactable_by_email',
            'contactable_by_phone', 'notes', 'archived', 'archived_on',
            'archived_reason', 'archived_by'
        )
        extra_kwargs = {
            'archived': {'read_only': True},
            'archived_on': {'read_only': True},
            'archived_reason': {'read_only': True},
            'archived_by': {'read_only': True}
        }
