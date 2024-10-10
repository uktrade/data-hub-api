from rest_framework import serializers

from datahub.company.models import Company
from datahub.core.serializers import (
    AddressSerializer,
    NestedRelatedField,
)
from datahub.investment_lead.models import EYBLead
from datahub.metadata.models import (
    AdministrativeArea,
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
    'sector_sub',
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
    'company_location',
    'full_name',
    'role',
    'email',
    'telephone_number',
    'agree_terms',
    'agree_info_email',
    'landing_timeframe',
    'company_website',
]

COMPANY_FIELDS = [
    'duns_number',
    'address_1',
    'address_2',
    'address_town',
    'address_county',
    'address_area',
    'address_country',
    'address_postcode',
    'company',
]

RELATED_FIELDS = [
    'sector',
    'location',
    'company_location',
    'address_area',
    'address_country',
    'company',
    'investment_projects',
]

ADDRESS_FIELDS = [
    'address_1',
    'address_2',
    'address_town',
    'address_county',
    'address_area',
    'address_country',
    'address_postcode',
]

UTM_FIELDS = [
    'utm_name',
    'utm_source',
    'utm_medium',
    'utm_content',
]

ALL_FIELDS = ARCHIVABLE_FIELDS + INVESTMENT_LEAD_BASE_FIELDS + \
    TRIAGE_FIELDS + USER_FIELDS + COMPANY_FIELDS + UTM_FIELDS

UUIDS_ERROR_MESSAGE = 'Invalid serializer data: UUIDs must match.'


class BaseEYBLeadSerializer(serializers.ModelSerializer):
    """Base serializer for an EYB lead object."""

    class Meta:
        model = EYBLead
        fields = ALL_FIELDS

    def validate(self, data):
        if data['triage_hashed_uuid'] != data['user_hashed_uuid']:
            raise serializers.ValidationError(UUIDS_ERROR_MESSAGE)
        return data


class CreateEYBLeadSerializer(BaseEYBLeadSerializer):
    """Serializer for creating an EYB lead.

    This serializer has been tailored to the data we expect to receive from EYB/DataFlow.
    Most notably, this includes string representations of related model instances.
    """

    class Meta(BaseEYBLeadSerializer.Meta):
        fields = [
            f for f in ALL_FIELDS
            if f not in ARCHIVABLE_FIELDS + INVESTMENT_LEAD_BASE_FIELDS + ['company']
        ]

    sector = serializers.CharField()
    location = serializers.CharField()
    company_location = serializers.CharField()
    address_area = serializers.CharField()
    address_country = serializers.CharField()

    # TODO: Refactor these field validation functions as they involve 5 db hits per lead
    def validate_sector(self, value):
        if not Sector.objects.filter(segment=value.capitalize()).exists():
            raise serializers.ValidationError(f'Sector "{value}" does not exist.')
        return value

    def validate_location(self, value):
        if not UKRegion.objects.filter(name=value.title()).exists():
            raise serializers.ValidationError(f'Location "{value}" does not exist.')
        return value

    def validate_company_location(self, value):
        if not Country.objects.filter(iso_alpha2_code=value.upper()).exists():
            raise serializers.ValidationError(
                f'Country location ISO code "{value}" does not exist.',
            )
        return value

    def validate_address_area(self, value):
        if not AdministrativeArea.objects.filter(name=value.capitalize()).exists():
            raise serializers.ValidationError(f'Address area "{value}" does not exist.')
        return value

    def validate_address_country(self, value):
        if not Country.objects.filter(iso_alpha2_code=value.upper()).exists():
            raise serializers.ValidationError(
                f'Address country ISO code "{value}" does not exist.',
            )
        return value

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        related_fields = {
            'sector': instance.sector.segment if instance.sector else None,
            'location': instance.location.name if instance.location else None,
            'company_location': instance.company_location.iso_alpha2_code
            if instance.company_location else None,
            'address_area': instance.address_area.name if instance.address_area else None,
            'address_country': instance.address_country.iso_alpha2_code
            if instance.address_country else None,
        }
        rep = super().to_representation(instance)
        rep.update(related_fields)
        return rep

    def to_internal_value(self, data):
        """Convert unvalidated JSON data to validated data."""
        # Extract related field strings
        sector_segment = data.get('sector', None)
        location_name = data.get('location', None)
        company_location_iso_code = data.get('company_location', None)
        address_area_name = data.get('address_area', None)
        address_country_iso_code = data.get('address_country', None)

        validated_data = super().to_internal_value(data)

        # Convert strings to model instances for related fields
        # TODO: Investigate refactoring this logic to involve less db hits (currently 5 per lead)
        if sector_segment:
            validated_data['sector'] = Sector.objects.get(
                segment=sector_segment.capitalize(),
            )
        if location_name:
            validated_data['location'] = UKRegion.objects.get(
                name=location_name.title(),
            )
        if company_location_iso_code:
            validated_data['company_location'] = Country.objects.get(
                iso_alpha2_code=company_location_iso_code.upper(),
            )
        if address_area_name:
            validated_data['address_area'] = AdministrativeArea.objects.get(
                name=address_area_name.capitalize(),
            )
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
    company_location = NestedRelatedField(Country)
    address = AddressSerializer(
        source_model=EYBLead,
        address_source_prefix='address',
    )
    company = NestedRelatedField(Company)
