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

UUIDS_ERROR_MESSAGE = 'Invalid serializer data: UUIDs must match.'


class EYBLeadSerializer(serializers.ModelSerializer):
    """Serializer for an EYB lead object"""

    triage_created = serializers.DateTimeField()
    triage_modified = serializers.DateTimeField()

    user_created = serializers.DateTimeField()
    user_modified = serializers.DateTimeField()

    class Meta:
        model = EYBLead
        fields = ALL_FIELDS

    def validate(self, data):
        if data['triage_hashed_uuid'] != data['user_hashed_uuid']:
            raise serializers.ValidationError(UUIDS_ERROR_MESSAGE)
        return data
