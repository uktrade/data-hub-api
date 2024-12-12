from django.db.models import Q
from rest_framework import serializers

from datahub.company.models import Company
from datahub.core.serializers import (
    AddressSerializer,
    NestedRelatedField,
)
from datahub.investment.project.models import InvestmentProject
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
    'proposed_investment_region',
    'proposed_investment_city',
    'proposed_investment_location_none',
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
    'proposed_investment_region',
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
    'marketing_hashed_uuid',
]

ALL_FIELDS = ARCHIVABLE_FIELDS + INVESTMENT_LEAD_BASE_FIELDS + \
    TRIAGE_FIELDS + USER_FIELDS + MARKETING_FIELDS


class BaseEYBLeadSerializer(serializers.ModelSerializer):
    """Base serializer for an EYB lead object.

    EYB serves data from 3 endpoints: triage, user and marketing.
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
    """Serializer for creating an EYB lead from triage data.

    This serializer uses camelCase field names to mirror those in the incoming data.
    Despite this being against Python convention (and Flake 8's checks), it was felt
    this was more readable, and potentially easier to maintain, than defining an additional
    step to translate them into snake_case names. The fields have `# noqa: N815` to tell
    flake 8 to ignore the camelCase check for these lines.

    As it currently stands, the lifecycle of incoming JSON data can roughly be defined as:

    1.  The unmodified incoming data passed to the serializer can be accessed at
        `.initial_data` and will have camelCase fields
    2.  Incoming data is passed through the to_internal_value() method (see BaseEYBLeadSerializer)
        where it's converted to Python objects. Any mappings/overrides specified in the
        get_related_fields_internal_value() method are applied at this step.
    3.  The resulting data is validated using any field or object level validators
        that are defined. If successful, `.validated_data` is accessible and contains snake_case
        field names (that match the model snake_case fields). Alternatively, any ValidationErrors
        are captured in `.errors`.
    """

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
    intent = serializers.ListField(required=False, allow_null=True, allow_empty=True, default=list)
    intentOther = serializers.CharField(  # noqa: N815
        source='intent_other', required=False, allow_null=True, allow_blank=True, default='',
    )
    location = serializers.CharField(
        source='proposed_investment_region', required=False, allow_null=True, allow_blank=True,
    )
    locationCity = serializers.CharField(  # noqa: N815
        source='proposed_investment_city',
        required=False, allow_null=True, allow_blank=True, default='',
    )
    locationNone = serializers.BooleanField(  # noqa: N815
        source='proposed_investment_location_none', required=False, allow_null=True,
    )
    hiring = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, default='',
    )
    spend = serializers.CharField(
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
            transformed_value = value.replace('_', ' ').title()
            if transformed_value == '':
                return None
            # Handle edge case where value is missing the word `The`
            if transformed_value == 'Yorkshire And Humber':
                transformed_value = 'Yorkshire and The Humber'
            if not UKRegion.objects.filter(name__iexact=transformed_value).exists():
                raise serializers.ValidationError(f'UK Region "{value}" does not exist.')
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
        # Sector could currently be disabled for historical leads
        queryset = Sector.objects.filter(
            Q(disabled_on__isnull=True) | Q(disabled_on__isnull=False),
        ).filter(segment__iexact=selected_segment)
        if parent_segment is not None:
            queryset.filter(parent__segment__iexact=parent_segment)
        sector = queryset.first()
        if isinstance(sector, Sector):
            internal_values['sector'] = sector
        internal_values['sector_segments'] = segments

        # Intent
        intent = data.get('intent', None)
        if intent is None:
            internal_values['intent'] = []

        # Proposed investment location
        uk_region_name = data.get('location', None)
        if isinstance(uk_region_name, str):
            uk_region = UKRegion.objects.filter(name=uk_region_name.title()).first()
            internal_values['proposed_investment_region'] = uk_region

        # Rest of the character fields
        char_fields = {
            'intentOther': 'intent_other',
            'locationCity': 'proposed_investment_city',
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
            Sector.get_segments_from_sector_instance(instance.sector)
        return {
            'sector': level_zero_segment,
            'sectorSub': level_one_segment,
            'sectorSubSub': level_two_segment,
            'location': instance.proposed_investment_region.name
            if instance.proposed_investment_region else None,
        }


class CreateEYBLeadUserSerializer(BaseEYBLeadSerializer):
    """Translates, validates, and creates an EYB lead from incoming user data.

    This serializer uses camelCase field names to mirror those in the incoming data.
    Despite this being against Python convention (and Flake 8's checks), it was felt
    this was more readable, and potentially easier to maintain, than defining an additional
    step to translate them into snake_case names. The fields have `# noqa: N815` to tell
    flake 8 to ignore the camelCase check for these lines.

    As it currently stands, the lifecycle of incoming JSON data can roughly be defined as:

    1.  The unmodified incoming data passed to the serializer can be accessed at
        `.initial_data` and will have camelCase fields
    2.  Incoming data is passed through the to_internal_value() method (see BaseEYBLeadSerializer)
        where it's converted to Python objects. Any mappings/overrides specified in the
        get_related_fields_internal_value() method are applied at this step.
    3.  The resulting data is validated using any field or object level validators
        that are defined. If successful, `.validated_data` is accessible and contains snake_case
        field names (that match the model snake_case fields). Alternatively, any ValidationErrors
        are captured in `.errors`.
    """

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
        source='duns_number', required=False, allow_null=True, allow_blank=True, default=None,
    )
    addressLine1 = serializers.CharField(source='address_1', required=True)  # noqa: N815
    addressLine2 = serializers.CharField(  # noqa: N815
        source='address_2', required=False, allow_null=True, allow_blank=True, default='',
    )
    town = serializers.CharField(source='address_town', required=True)
    county = serializers.CharField(
        source='address_county', required=False, allow_null=True, allow_blank=True, default='',
    )
    companyLocation = serializers.CharField(source='address_country', required=True)  # noqa: N815
    postcode = serializers.CharField(
        source='address_postcode', required=False, allow_null=True, allow_blank=True, default='',
    )
    companyWebsite = serializers.CharField(  # noqa: N815
        source='company_website', required=False, allow_null=True, allow_blank=True, default='',
    )
    fullName = serializers.CharField(source='full_name', required=True)  # noqa: N815
    role = serializers.CharField(required=False, allow_null=True, allow_blank=True, default='')
    email = serializers.CharField(required=True)
    telephoneNumber = serializers.CharField(  # noqa: N815
        source='telephone_number', required=False, allow_null=True, allow_blank=True, default='',
    )
    agreeTerms = serializers.BooleanField(  # noqa: N815
        source='agree_terms', required=False, allow_null=True, default=None,
    )
    agreeInfoEmail = serializers.BooleanField(  # noqa: N815
        source='agree_info_email', required=False, allow_null=True, default=None,
    )
    landingTimeframe = serializers.CharField(  # noqa: N815
        source='landing_timeframe',
        required=False,
        allow_null=True,
        allow_blank=True,
        default='',
    )

    def validate_companyLocation(self, value):  # noqa: N802
        if not Country.objects.filter(iso_alpha2_code=value.upper()).exists():
            raise serializers.ValidationError(
                f'Company location/country ISO2 code "{value.upper()}" does not exist.',
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
            if value == '':
                internal_values[internal_field] = None

        # Rest of the character fields
        char_fields = {
            'addressLine2': 'address_2',
            'county': 'address_county',
            'postcode': 'address_postcode',
            'companyWebsite': 'company_website',
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


class CreateEYBLeadMarketingSerializer(BaseEYBLeadSerializer):
    class Meta(BaseEYBLeadSerializer.Meta):
        fields = [
            'name',
            'medium',
            'source',
            'content',
            'hashed_uuid',
        ]

    name = serializers.CharField(
        source='utm_name', required=False, allow_null=True, allow_blank=True, default='',
    )
    medium = serializers.CharField(
        source='utm_medium', required=False, allow_null=True, allow_blank=True, default='',
    )
    source = serializers.CharField(
        source='utm_source', required=False, allow_null=True, allow_blank=True, default='',
    )
    content = serializers.CharField(
        source='utm_content', required=False, allow_null=True, allow_blank=True, default='',
    )
    hashed_uuid = serializers.CharField(source='marketing_hashed_uuid', required=True)

    def get_related_fields_internal_value(self, data):
        """Provides related fields in a format suitable for internal use."""
        internal_values = {}

        # Character fields
        char_fields = {
            'name': 'utm_name',
            'medium': 'utm_medium',
            'source': 'utm_source',
            'content': 'utm_content',
        }
        for incoming_field, internal_field in char_fields.items():
            value = data.get(incoming_field, None)
            if value is None:
                internal_values[internal_field] = ''

        return internal_values


class RetrieveEYBLeadSerializer(BaseEYBLeadSerializer):

    class Meta(BaseEYBLeadSerializer.Meta):
        fields = [
            f for f in ALL_FIELDS
            if f not in ADDRESS_FIELDS
        ] + ['address', 'investment_projects']

    sector = NestedRelatedField(Sector)
    proposed_investment_region = NestedRelatedField(UKRegion)
    address = AddressSerializer(
        source_model=EYBLead,
        address_source_prefix='address',
    )
    company = NestedRelatedField(Company)
    investment_projects = NestedRelatedField(InvestmentProject, many=True)
