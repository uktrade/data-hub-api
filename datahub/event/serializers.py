from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.core.constants import Country
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import DataCombiner
from datahub.event.models import Event


class EventSerializer(serializers.ModelSerializer):
    """Event serialiser."""

    default_error_messages = {
        'lead_team_not_in_teams': ugettext_lazy('Lead team must be in teams array.'),
        'end_date_without_start_date': ugettext_lazy('Cannot have an end date without a start '
                                                     'date.'),
        'end_date_before_start_date': ugettext_lazy('End date cannot be before start date.'),
        'uk_region_non_uk_country': ugettext_lazy('Cannot specify a UK region for a non-UK '
                                                  'country.')
    }

    event_type = NestedRelatedField('event.EventType')
    location_type = NestedRelatedField('event.LocationType', required=False, allow_null=True)
    organiser = NestedAdviserField(required=False, allow_null=True)
    lead_team = NestedRelatedField('metadata.Team', required=False, allow_null=True)
    teams = NestedRelatedField('metadata.Team', many=True, required=False, allow_empty=True)
    address_country = NestedRelatedField('metadata.Country')
    uk_region = NestedRelatedField('metadata.UKRegion', required=False, allow_null=True)
    related_programmes = NestedRelatedField(
        'event.Programme', many=True, required=False, allow_empty=True
    )
    service = NestedRelatedField('metadata.Service')

    def validate(self, data):
        """Performs cross-field validation."""
        errors = {}
        combiner = DataCombiner(self.instance, data)

        validators = (
            self._validate_lead_team,
            self._validate_dates,
            self._validate_uk_region,
        )

        for validator in validators:
            errors.update(validator(combiner))

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def _validate_lead_team(self, combiner):
        errors = {}
        lead_team = combiner.get_value('lead_team')
        teams = combiner.get_value_to_many('teams')

        if lead_team and lead_team not in teams:
            errors['lead_team'] = self.error_messages['lead_team_not_in_teams']

        return errors

    def _validate_dates(self, combiner):
        errors = {}
        start_date = combiner.get_value('start_date')
        end_date = combiner.get_value('end_date')

        if end_date:
            if not start_date:
                errors['end_date'] = self.error_messages['end_date_without_start_date']
            elif end_date < start_date:
                errors['end_date'] = self.error_messages['end_date_before_start_date']

        return errors

    def _validate_uk_region(self, combiner):
        errors = {}
        address_country_id = combiner.get_value_id('address_country')
        uk_region = combiner.get_value('uk_region')

        if address_country_id is None:
            return errors

        is_uk = address_country_id == Country.united_kingdom.value.id

        if is_uk and not uk_region:
            errors['uk_region'] = self.error_messages['required']
        elif not is_uk and uk_region:
            errors['uk_region'] = self.error_messages['uk_region_non_uk_country']

        return errors

    class Meta:  # noqa: D101
        model = Event
        fields = (
            'address_1',
            'address_2',
            'address_country',
            'address_country',
            'address_county',
            'address_postcode',
            'address_town',
            'uk_region',
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
            'service',
        )
