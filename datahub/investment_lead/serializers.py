from rest_framework import serializers

from datahub.company.models import Company
from datahub.core.serializers import (
    AddressSerializer,
    NestedRelatedField,
)
from datahub.investment_lead.models import EYBLead
from datahub.metadata.models import (
    Country,
    Sector,
    UKRegion,
)


ARCHIVABLE_FIELDS = [
    'archived',
    'archived_on',
    'archived_reason',
    'archived_by',
]

INVESTMENT_LEAD_BASE_FIELDS = [
    'created_on',
    'modified_on',
    'id',
]

TRIAGE_FIELDS = [
    'triage_hashed_uuid',
    'triage_created',
    'triage_modified',
    'sector',
    'intent',
    'intent_other',
    'location',
    'location_city',
    'location_none',
    'hiring',
    'spend',
    'spend_other',
    'is_high_value',
]

USER_FIELDS = [
    'user_hashed_uuid',
    'user_created',
    'user_modified',
    'company_name',
    'duns_number',
    'address_1',
    'address_2',
    'address_town',
    'address_country',
    'address_postcode',
    'company_website',
    'company',
    'full_name',
    'role',
    'email',
    'telephone_number',
    'agree_terms',
    'agree_info_email',
    'landing_timeframe',
]

RELATED_FIELDS = [
    'sector',
    'location',
    'address_country',
    'company',
    'investment_projects',
]

ADDRESS_FIELDS = [
    'address_1',
    'address_2',
    'address_town',
    'address_country',
    'address_postcode',
]

MARKETING_FIELDS = [
    'utm_name',
    'utm_source',
    'utm_medium',
    'utm_content',
]

ALL_FIELDS = ARCHIVABLE_FIELDS + INVESTMENT_LEAD_BASE_FIELDS + \
    TRIAGE_FIELDS + USER_FIELDS + MARKETING_FIELDS


class BaseEYBLeadSerializer(serializers.ModelSerializer):
    """Base serializer for an EYB lead object.

    EYB serves data from 2 endpoints: triage and user.
    However, in Data Hub, we combine them into one EYB lead model instance.
    """

    class Meta:
        model = EYBLead
        fields = []


class CreateEYBLeadTriageSerializer(BaseEYBLeadSerializer):
    """Serializer for creating an EYB lead from triage data."""

    class Meta(BaseEYBLeadSerializer.Meta):
        fields = TRIAGE_FIELDS
        extra_kwargs = {
            'triage_hashed_uuid': {'required': True},
            'triage_created': {'required': True},
            'triage_modified': {'required': True},
            'sector': {'required': True},
            'intent': {'required': True},
            'intent_other': {'required': True},
            'location': {'required': True},
            'location_city': {'required': True},
            'location_none': {'required': True},
            'hiring': {'required': True},
            'spend': {'required': True},
            'spend_other': {'required': True},
            'is_high_value': {'required': True},
        }

    sector = serializers.CharField()
    location = serializers.CharField()

    # TODO: Refactor these field validation functions as they involve 2 db hits per record
    def validate_sector(self, value):
        if not Sector.objects.filter(segment=value.capitalize()).exists():
            raise serializers.ValidationError(f'Sector "{value}" does not exist.')
        return value

    def validate_location(self, value):
        if not UKRegion.objects.filter(name=value.title()).exists():
            raise serializers.ValidationError(f'Location "{value}" does not exist.')
        return value

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        related_fields = {
            'sector': instance.sector.segment if instance.sector else None,
            'location': instance.location.name if instance.location else None,
        }
        rep = super().to_representation(instance)
        rep.update(related_fields)
        return rep

    def to_internal_value(self, data):
        """Convert unvalidated JSON data to validated data."""
        # Extract related field strings
        sector_segment = data.get('sector', None)
        location_name = data.get('location', None)

        validated_data = super().to_internal_value(data)

        # Convert strings to model instances for related fields
        # TODO: Investigate refactoring this logic to involve less db hits (currently 2 per record)
        # TODO: Handle case where segment returns multiple sectors (e.g. Sensors)
        if sector_segment:
            validated_data['sector'] = Sector.objects.get(
                segment=sector_segment.capitalize(),
            )
        if location_name:
            validated_data['location'] = UKRegion.objects.get(
                name=location_name.title(),
            )
        return validated_data


class CreateEYBLeadUserSerializer(BaseEYBLeadSerializer):
    """Serializer for creating an EYB lead from user data."""

    class Meta(BaseEYBLeadSerializer.Meta):
        fields = USER_FIELDS
        extra_kwargs = {
            'user_hashed_uuid': {'required': True},
            'user_created': {'required': True},
            'user_modified': {'required': True},
            'company_name': {'required': True},
            'duns_number': {'required': True},
            'address_1': {'required': True},
            'address_2': {'required': True},
            'address_town': {'required': True},
            'address_country': {'required': True},
            'address_postcode': {'required': True},
            'company_website': {'required': True},
            'full_name': {'required': True},
            'role': {'required': True},
            'email': {'required': True},
            'telephone_number': {'required': True},
            'agree_terms': {'required': True},
            'agree_info_email': {'required': True},
            'landing_timeframe': {'required': True},
        }

    address_country = serializers.CharField()

    # TODO: Refactor these field validation functions as they involve 1 db hit per record
    def validate_address_country(self, value):
        if not Country.objects.filter(iso_alpha2_code=value.upper()).exists():
            raise serializers.ValidationError(
                f'Address country ISO code "{value}" does not exist.',
            )
        return value

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        related_fields = {
            'address_country': instance.address_country.iso_alpha2_code
            if instance.address_country else None,
        }
        rep = super().to_representation(instance)
        rep.update(related_fields)
        return rep

    def to_internal_value(self, data):
        """Convert unvalidated JSON data to validated data."""
        # Extract related field strings
        address_country_iso_code = data.get('address_country', None)

        validated_data = super().to_internal_value(data)

        # Convert strings to model instances for related fields
        # TODO: Investigate refactoring this logic to involve less db hits (currently 1 per record)
        if address_country_iso_code:
            validated_data['address_country'] = Country.objects.get(
                iso_alpha2_code=address_country_iso_code.upper(),
            )
        return validated_data


class RetrieveEYBLeadSerializer(BaseEYBLeadSerializer):

    class Meta(BaseEYBLeadSerializer.Meta):
        fields = [
            f for f in ALL_FIELDS
            if f not in ADDRESS_FIELDS
        ] + ['address']

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types.

        Specifically, we want to convert `UPPER_CASE` values to `Sentence case` labels
        for choice fields.
        """
        related_fields = {
            'intent': [
                EYBLead.IntentChoices(intent_choice).label
                for intent_choice in instance.intent
            ],
            'hiring': EYBLead.HiringChoices(instance.hiring).label,
            'spend': EYBLead.SpendChoices(instance.spend).label,
            'landing_timeframe': EYBLead.LandingTimeframeChoices(
                instance.landing_timeframe,
            ).label,
        }
        rep = super().to_representation(instance)
        rep.update(related_fields)
        return rep

    sector = NestedRelatedField(Sector)
    location = NestedRelatedField(UKRegion)
    address = AddressSerializer(
        source_model=EYBLead,
        address_source_prefix='address',
    )
    company = NestedRelatedField(Company)
