from rest_framework import serializers

from datahub.investment_lead.models import EYBLead


ALL_FIELDS = [
    'triage_id',
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
    'user_id',
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


class EYBLeadSerializer(serializers.ModelSerializer):
    """Serializer for an EYB lead object"""

    triage_created = serializers.DateTimeField(read_only=True)
    triage_modified = serializers.DateTimeField(read_only=True)

    user_created = serializers.DateTimeField(read_only=True)
    user_modified = serializers.DateTimeField(read_only=True)

    class Meta:
        model = EYBLead
        fields = ALL_FIELDS
