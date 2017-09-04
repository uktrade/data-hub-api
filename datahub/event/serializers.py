from rest_framework import serializers

from datahub.core.serializers import NestedRelatedField
from datahub.event.models import Event


class EventSerializer(serializers.ModelSerializer):
    """Event serialiser."""

    event_type = NestedRelatedField('event.EventType')
    location_type = NestedRelatedField('event.LocationType', required=False, allow_null=True)
    lead_team = NestedRelatedField('metadata.Team', required=False, allow_null=True)
    additional_teams = NestedRelatedField(
        'metadata.Team', many=True, required=False, allow_empty=True
    )
    address_country = NestedRelatedField('metadata.Country')
    related_programmes = NestedRelatedField(
        'event.Programme', many=True, required=False, allow_empty=True
    )

    class Meta:  # noqa: D101
        model = Event
        extra_kwargs = {
            # As these don't have null=True, DRF defaults to required=True
            'address_2': {'required': False},
            'address_postcode': {'required': False},
            'notes': {'required': False},
        }
        fields = (
            'additional_teams',
            'address_1',
            'address_2',
            'address_country',
            'address_country',
            'address_county',
            'address_postcode',
            'address_town',
            'end_date',
            'event_type',
            'id',
            'lead_team',
            'location_type',
            'name',
            'notes',
            'related_programmes',
            'start_date',
        )
