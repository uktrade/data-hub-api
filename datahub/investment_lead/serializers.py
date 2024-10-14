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

    def to_internal_value(self, data):
        """Convert unvalidated JSON data to validated data."""
        internal_value = super().to_internal_value(data)
        related_fields = self.get_related_fields_internal_value(data)
        internal_value.update(related_fields)
        return internal_value

    def get_related_fields_internal_value(self, data):
        """Provides related fields in a format suitable for internal use; override as needed."""
        return {}

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        representation = super().to_representation(instance)
        related_fields = self.get_related_fields_representation(instance)
        representation.update(related_fields)
        return representation

    def get_related_fields_representation(self, instance):
        """Provides related fields in a representation-friendly format; override as needed."""
        return {}


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
            'sector_segments',  # snake_case as referring to model field directly
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
    sectorSub = serializers.CharField(  # noqa: N815
        read_only=True, required=False, allow_null=True,
    )
    sectorSubSub = serializers.CharField(  # noqa: N815
        read_only=True, required=False, allow_null=True,
    )
    # Can't use MultipleChoiceField here as it returns a set rather than a list and raises db error
    intent = serializers.ListField(required=False, allow_null=True, allow_empty=True, default=list)
    intentOther = serializers.CharField(  # noqa: N815
        source='intent_other', required=False, allow_null=True, allow_blank=True, default='',
    )
    location = serializers.CharField(required=False, allow_null=True)
    locationCity = serializers.CharField(  # noqa: N815
        source='location_city', required=False, allow_null=True, allow_blank=True, default='',
    )
    locationNone = serializers.BooleanField(  # noqa: N815
        source='location_none', required=False, allow_null=True,
    )
    hiring = serializers.ChoiceField(
        choices=EYBLead.HiringChoices.choices,
        required=False, allow_null=True, allow_blank=True, default='',
    )
    spend = serializers.ChoiceField(
        choices=EYBLead.SpendChoices.choices,
        required=False, allow_null=True, allow_blank=True, default='',
    )
    spendOther = serializers.CharField(  # noqa: N815
        source='spend_other', required=False, allow_null=True, allow_blank=True, default='',
    )
    isHighValue = serializers.BooleanField(  # noqa: N815
        source='is_high_value', required=False, allow_null=True,
    )

    def validate_location(self, value):
        if isinstance(value, str):
            if not UKRegion.objects.filter(name=value.title()).exists():
                raise serializers.ValidationError(f'Location "{value}" does not exist.')
        return value

    def validate(self, data):
        """Validate sector data.

        At this stage, the data has passed through the to_internal_value()
        method and the sector field will be a sector instance if valid,
        or the original string if invalid (see get_related_fields_internal_value).

        Note, the sectorSub and sectorSubSub fields are not in the dictionary at
        this stage.
        """
        sector = data.get('sector')
        if not isinstance(sector, Sector):
            segments = data.get('sector_segments')
            sector_name = Sector.get_name_from_segments(segments)
            raise serializers.ValidationError(f'Sector "{sector_name}" does not exist.')
        return data

    def get_related_fields_internal_value(self, data):
        """Provides related fields in a format suitable for internal use."""
        internal_values = {}

        # Sector
        segments = [
            data.get('sector', None),
            data.get('sectorSub', None),
            data.get('sectorSubSub', None),
        ]
        sector_name = Sector.get_name_from_segments(segments)
        selected_segment, parent_segment = Sector.get_selected_and_parent_segments(sector_name)
        queryset = Sector.objects.filter(segment=selected_segment)
        if parent_segment is not None:
            queryset.filter(parent__segment=parent_segment)
        sector = queryset.first()
        if isinstance(sector, Sector):
            internal_values['sector'] = sector
        internal_values['sector_segments'] = segments

        # Intent
        intent = data.get('intent', None)
        if intent is None:
            internal_values['intent'] = []

        # Location
        location_name = data.get('location', None)
        if isinstance(location_name, str):
            location = UKRegion.objects.filter(name=location_name.title()).first()
            if isinstance(location, UKRegion):
                internal_values['location'] = location

        # Rest of the character fields
        char_fields = {
            'intentOther': 'intent_other',
            'locationCity': 'location_city',
            'hiring': 'hiring',
            'spend': 'spend',
            'spendOther': 'spend_other',
        }
        for incoming_field, internal_field in char_fields.items():
            value = data.get(incoming_field, None)
            if value is None:
                internal_values[internal_field] = ''

        return internal_values

    def get_related_fields_representation(self, instance):
        """Provides related fields in a representation-friendly format."""
        level_zero_segment, level_one_segment, level_two_segment = \
            get_segments_from_sector_instance(instance.sector)
        return {
            'sector': level_zero_segment,
            'sectorSub': level_one_segment,
            'sectorSubSub': level_two_segment,
            'location': instance.location.name if instance.location else None,
        }


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
            'county',
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
    dunsNumber = serializers.CharField(  # noqa: N815
        source='duns_number', required=False, allow_null=True, default=None,
    )
    addressLine1 = serializers.CharField(source='address_1', required=True)  # noqa: N815
    addressLine2 = serializers.CharField(  # noqa: N815
        source='address_2', required=False, allow_null=True, default='',
    )
    town = serializers.CharField(source='address_town', required=True)
    county = serializers.CharField(
        source='address_county', required=False, allow_null=True, default='',
    )
    companyLocation = serializers.CharField(source='address_country', required=True)  # noqa: N815
    postcode = serializers.CharField(
        source='address_postcode', required=False, allow_null=True, default='',
    )
    companyWebsite = serializers.CharField(  # noqa: N815
        source='company_website', required=False, allow_null=True, default='',
    )
    fullName = serializers.CharField(source='full_name', required=True)  # noqa: N815
    role = serializers.CharField(required=False, allow_null=True, default='')
    email = serializers.CharField(required=True)
    telephoneNumber = serializers.CharField(  # noqa: N815
        source='telephone_number', required=False, allow_null=True, default='',
    )
    agreeTerms = serializers.BooleanField(  # noqa: N815
        source='agree_terms', required=False, allow_null=True, default=None,
    )
    agreeInfoEmail = serializers.BooleanField(  # noqa: N815
        source='agree_info_email', required=False, allow_null=True, default=None,
    )
    landingTimeframe = serializers.ChoiceField(  # noqa: N815
        source='landing_timeframe',
        choices=EYBLead.LandingTimeframeChoices.choices,
        required=False,
        allow_null=True,
        default='',
    )

    def validate_companyLocation(self, value):  # noqa: N802
        if not Country.objects.filter(iso_alpha2_code=value.upper()).exists():
            raise serializers.ValidationError(
                f'Company location/country ISO2 code "{value}" does not exist.',
            )
        return value

    def get_related_fields_internal_value(self, data):
        """Provides related fields in a format suitable for internal use."""
        internal_values = {}

        # Company location / address country
        address_country_iso_code = data.get('companyLocation', None)
        internal_values['address_country'] = Country.objects.get(
            iso_alpha2_code=address_country_iso_code.upper(),
        )

        # Fields that can be None
        none_fields = {
            'dunsNumber': 'duns_number',
            'agreeTerms': 'agree_terms',
            'agreeInfoEmail': 'agree_info_email',
        }
        for incoming_field, internal_field in none_fields.items():
            value = data.get(incoming_field, None)
            if value is None:
                internal_values[internal_field] = None

        # Rest of the character fields
        char_fields = {
            'dunsNumber': 'duns_number',
            'addressLine2': 'address_2',
            'county': 'address_county',
            'postcode': 'address_postcode',
            'role': 'role',
            'telphoneNumber': 'telephone_number',
            'landingTimeframe': 'landing_timeframe',
        }
        for incoming_field, internal_field in char_fields.items():
            value = data.get(incoming_field, None)
            if value is None:
                internal_values[internal_field] = ''

        return internal_values

    def get_related_fields_representation(self, instance):
        """Provides related fields in a representation-friendly format."""
        return {
            'companyLocation': instance.address_country.iso_alpha2_code
            if instance.address_country else None,
        }


class RetrieveEYBLeadSerializer(BaseEYBLeadSerializer):

    class Meta(BaseEYBLeadSerializer.Meta):
        fields = [
            f for f in ALL_FIELDS
            if f not in ADDRESS_FIELDS
        ] + ['address']

    sector = NestedRelatedField(Sector)
    location = NestedRelatedField(UKRegion)
    address = AddressSerializer(
        source_model=EYBLead,
        address_source_prefix='address',
    )
    company = NestedRelatedField(Company)

    def get_related_fields_representation(self, instance):
        """Provides related fields in a representation-friendly format.

        Specifically, we want to convert `UPPER_CASE` values to `Sentence case` labels
        for choice fields.
        """
        return {
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
