from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import DataCombiner
from datahub.event.models import Event


class EventSerializer(serializers.ModelSerializer):
    """Event serialiser."""

    default_error_messages = {
        'lead_team_not_in_teams': ugettext_lazy('Lead team must be in teams array.'),
    }

    event_type = NestedRelatedField('event.EventType')
    location_type = NestedRelatedField('event.LocationType', required=False, allow_null=True)
    organiser = NestedAdviserField(required=False, allow_null=True)
    lead_team = NestedRelatedField('metadata.Team', required=False, allow_null=True)
    teams = NestedRelatedField('metadata.Team', many=True, required=False, allow_empty=True)
    address_country = NestedRelatedField('metadata.Country')
    related_programmes = NestedRelatedField(
        'event.Programme', many=True, required=False, allow_empty=True
    )

    def validate(self, data):
        """Performs lead team/team cross-field validation."""
        combiner = DataCombiner(self.instance, data)
        lead_team = combiner.get_value('lead_team')
        teams = combiner.get_value_to_many('teams')

        if lead_team and lead_team not in teams:
            raise serializers.ValidationError({
                'lead_team': self.error_messages['lead_team_not_in_teams']
            })

        return data

    class Meta:  # noqa: D101
        model = Event
        extra_kwargs = {
            # As these don't have null=True, DRF defaults to required=True
            'address_2': {'required': False},
            'address_postcode': {'required': False},
            'notes': {'required': False},
        }
        fields = (
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
            'organiser',
            'related_programmes',
            'start_date',
            'teams',
        )
