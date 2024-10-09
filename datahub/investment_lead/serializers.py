from rest_framework import serializers

from datahub.company.models import Company
from datahub.core.serializers import (
    AddressSerializer,
    NestedRelatedField,
)
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.conftest import get_segments_from_sector_instance
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
        fields = [
            'hashedUuid',
            'created',
            'modified',
            'sector',
            'sectorSub',
            'sectorSubSub',
            'intent',
            'intentOther',
            'location',
            'locationCity',
            'locationNone',
            'hiring',
            'spend',
            'spendOther',
            'isHighValue',
        ]

    hashedUuid = serializers.CharField(source='triage_hashed_uuid', required=True)  # noqa: N815
    created = serializers.DateTimeField(source='triage_created', required=True)
    modified = serializers.DateTimeField(source='triage_modified', required=True)
    sector = serializers.CharField(required=True)
    sectorSub = serializers.CharField(required=False, allow_null=True)  # noqa: N815
    sectorSubSub = serializers.CharField(required=False, allow_null=True)  # noqa: N815
    # Can't use MultipleChoiceField here as it returns a set rather than a list and raises db error
    intent = serializers.ListField(required=True)
    intentOther = serializers.CharField(  # noqa: N815
        source='intent_other', required=True, allow_blank=True,
    )
    location = serializers.CharField(required=True)
    locationCity = serializers.CharField(source='location_city', required=True)  # noqa: N815
    locationNone = serializers.BooleanField(source='location_none', required=True)  # noqa: N815
    hiring = serializers.ChoiceField(
        required=True, choices=EYBLead.HiringChoices.choices,
    )
    spend = serializers.ChoiceField(
        required=True, choices=EYBLead.SpendChoices.choices,
    )
    spendOther = serializers.CharField(  # noqa: N815
        source='spend_other', required=True, allow_blank=True,
    )
    isHighValue = serializers.BooleanField(source='is_high_value', required=True)  # noqa: N815

    def validate_location(self, value):
        if not UKRegion.objects.filter(name=value.title()).exists():
            raise serializers.ValidationError(f'Location "{value}" does not exist.')
        return value

    def _get_sector_instance_from_segments(
        self,
        level_zero_segment,
        level_one_segment,
        level_two_segment,
    ):
        """Looks up and returns a sector instance given the individual level segments."""
        # Determine selected sector and parent name
        if level_two_segment:
            selected_sector_segment = level_two_segment
            parent_sector_segment = level_one_segment
        elif level_one_segment:
            selected_sector_segment = level_one_segment
            parent_sector_segment = level_zero_segment
        elif level_zero_segment:
            selected_sector_segment = level_zero_segment
            parent_sector_segment = None

        # Filter based on found names
        queryset = Sector.objects.filter(segment=selected_sector_segment)
        if parent_sector_segment is not None:
            queryset.filter(parent__segment=parent_sector_segment)

        # Raise validation error if no sectors matched
        if not queryset.exists():
            full_name = ' : '.join([
                segment for segment in [level_zero_segment, level_one_segment, level_two_segment]
                if segment is not None
            ])
            raise serializers.ValidationError(f'Sector "{full_name}" does not exist.')
        return queryset.first()

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        level_zero_segment, level_one_segment, level_two_segment = \
            get_segments_from_sector_instance(instance.sector)
        related_fields = {
            'sector': level_zero_segment,
            'sectorSub': level_one_segment,
            'sectorSubSub': level_two_segment,
            'location': instance.location.name if instance.location else None,
        }
        rep = super().to_representation(instance)
        rep.update(related_fields)
        return rep

    def to_internal_value(self, data):
        """Convert unvalidated JSON data to validated data."""
        # Extract strings from incoming JSON for related fields
        # Using .get() here as field is required by serializer/model
        level_zero_segment = data.get('sector', None)
        # Using .pop() here otherwise error is raised when calling serializer.save()
        level_one_segment = data.pop('sectorSub', None)
        level_two_segment = data.pop('sectorSubSub', None)

        location_name = data.get('location', None)

        # Convert and validate rest of the data
        validated_data = super().to_internal_value(data)

        # Convert strings to model instances for related fields and overwrite validated data
        validated_data['sector'] = self._get_sector_instance_from_segments(
            level_zero_segment,
            level_one_segment,
            level_two_segment,
        )
        if location_name:
            validated_data['location'] = UKRegion.objects.get(
                name=location_name.title(),
            )
        return validated_data


class CreateEYBLeadUserSerializer(BaseEYBLeadSerializer):
    """Serializer for creating an EYB lead from user data."""

    class Meta(BaseEYBLeadSerializer.Meta):
        fields = [
            'hashedUuid',
            'created',
            'modified',
            'companyName',
            'dunsNumber',
            'addressLine1',
            'addressLine2',
            'town',
            'companyLocation',
            'postcode',
            'companyWebsite',
            'fullName',
            'role',
            'email',
            'telephoneNumber',
            'agreeTerms',
            'agreeInfoEmail',
            'landingTimeframe',
        ]

    hashedUuid = serializers.CharField(source='user_hashed_uuid', required=True)  # noqa: N815
    created = serializers.DateTimeField(source='user_created', required=True)
    modified = serializers.DateTimeField(source='user_modified', required=True)
    companyName = serializers.CharField(source='company_name', required=True)  # noqa: N815
    dunsNumber = serializers.CharField(source='duns_number', required=True)  # noqa: N815
    addressLine1 = serializers.CharField(source='address_1', required=True)  # noqa: N815
    addressLine2 = serializers.CharField(source='address_2', required=False)  # noqa: N815
    town = serializers.CharField(source='address_town', required=True)
    companyLocation = serializers.CharField(source='address_country', required=True)  # noqa: N815
    postcode = serializers.CharField(source='address_postcode', required=True)
    companyWebsite = serializers.CharField(source='company_website', required=True)  # noqa: N815
    fullName = serializers.CharField(source='full_name', required=True)  # noqa: N815
    role = serializers.CharField(required=True)
    email = serializers.CharField(required=True)
    telephoneNumber = serializers.CharField(source='telephone_number', required=True)  # noqa: N815
    agreeTerms = serializers.BooleanField(source='agree_terms', required=True)  # noqa: N815
    agreeInfoEmail = serializers.BooleanField(  # noqa: N815
        source='agree_info_email', required=True,
    )
    landingTimeframe = serializers.ChoiceField(  # noqa: N815
        source='landing_timeframe',
        required=True,
        choices=EYBLead.LandingTimeframeChoices.choices,
    )

    def validate_address_country(self, value):
        if not Country.objects.filter(iso_alpha2_code=value.upper()).exists():
            raise serializers.ValidationError(
                f'Address country ISO code "{value}" does not exist.',
            )
        return value

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        related_fields = {
            'companyLocation': instance.address_country.iso_alpha2_code
            if instance.address_country else None,
        }
        rep = super().to_representation(instance)
        rep.update(related_fields)
        return rep

    def to_internal_value(self, data):
        """Convert unvalidated JSON data to validated data."""
        # Extract strings from incoming JSON for related fields
        address_country_iso_code = data.get('companyLocation', None)

        # Convert and validate rest of the data
        validated_data = super().to_internal_value(data)

        # Convert strings to model instances for related fields and overwrite validated data
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
