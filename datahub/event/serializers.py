from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.core.constants import Country
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import DataCombiner
from datahub.event.models import Event
from datahub.metadata.serializers import SERVICE_LEAF_NODE_NOT_SELECTED_MESSAGE


class BaseEventSerializer(serializers.ModelSerializer):
    """Common functionality between V3 and V4 endpoint"""

    default_error_messages = {
        'lead_team_not_in_teams': gettext_lazy('Lead team must be in teams array.'),
        'end_date_before_start_date': gettext_lazy('End date cannot be before start date.'),
        'uk_region_non_uk_country': gettext_lazy(
            'Cannot specify a UK region for a non-UK country.',
        ),
    }
    end_date = serializers.DateField()
    event_type = NestedRelatedField('event.EventType')
    location_type = NestedRelatedField('event.LocationType', required=False, allow_null=True)
    organiser = NestedAdviserField()
    lead_team = NestedRelatedField('metadata.Team')
    teams = NestedRelatedField('metadata.Team', many=True, allow_empty=False)
    address_country = NestedRelatedField('metadata.Country')
    uk_region = NestedRelatedField('metadata.UKRegion', required=False, allow_null=True)
    related_programmes = NestedRelatedField(
        'event.Programme', many=True, required=False, allow_empty=True,
    )
    service = NestedRelatedField('metadata.Service')
    start_date = serializers.DateField()

    def validate_service(self, value):
        """Make sure only a service without children can be assigned."""
        if value and value.children.count() > 0:
            raise serializers.ValidationError(SERVICE_LEAF_NODE_NOT_SELECTED_MESSAGE)
        return value

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

        if lead_team not in teams:
            errors['lead_team'] = self.error_messages['lead_team_not_in_teams']

        return errors

    def _validate_dates(self, combiner):
        errors = {}

        start_date = combiner.get_value('start_date')
        end_date = combiner.get_value('end_date')

        if start_date and end_date and end_date < start_date:
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


class EventSerializer(BaseEventSerializer):
    """Event serialiser for V3 endpoint."""

    related_trade_agreements = NestedRelatedField(
        'metadata.TradeAgreement', many=True, required=False, allow_empty=True,
    )

    class Meta:
        model = Event
        fields = (
            'address_1',
            'address_2',
            'address_country',
            'address_country',
            'address_county',
            'address_postcode',
            'address_town',
            'archived_documents_url_path',
            'disabled_on',
            'end_date',
            'event_type',
            'id',
            'lead_team',
            'location_type',
            'name',
            'notes',
            'organiser',
            'has_related_trade_agreements',
            'related_trade_agreements',
            'related_programmes',
            'start_date',
            'teams',
            'service',
            'uk_region',
        )
        read_only_fields = (
            'archived_documents_url_path',
            'disabled_on',
        )


class EventSerializerV4(BaseEventSerializer):
    """Event serialiser for V4 endpoint."""

    default_error_messages = {
        'related_trade_agreements':
            gettext_lazy(
                "'Related trade agreements' is inconsistent with 'Has related trade agreements?'",
            ),
    }

    has_related_trade_agreements = serializers.BooleanField(required=True)
    related_trade_agreements = NestedRelatedField(
        'metadata.TradeAgreement', many=True, required=True, allow_empty=True,
    )

    def validate(self, attrs):
        """Performs cross-field validation."""
        attrs = super().validate(attrs)

        errors = {}
        combiner = DataCombiner(self.instance, attrs)

        validators = (
            self._validate_related_trade_agreements,
        )
        for validator in validators:
            errors.update(validator(combiner))

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def _validate_related_trade_agreements(self, combiner):
        """Validates trade agreement state for consistency with has_related_trade_agreements"""
        errors = {}
        related_trade_agreements_count = len(
            combiner.get_value_to_many('related_trade_agreements'),
        )
        has_related_trade_agreements = combiner.get_value('has_related_trade_agreements')

        if (related_trade_agreements_count == 0 and has_related_trade_agreements) or (
                related_trade_agreements_count > 0 and not has_related_trade_agreements):
            errors['related_trade_agreements'] = self.error_messages['related_trade_agreements']
        return errors

    class Meta:
        model = Event
        fields = (
            'address_1',
            'address_2',
            'address_country',
            'address_country',
            'address_county',
            'address_postcode',
            'address_town',
            'archived_documents_url_path',
            'disabled_on',
            'end_date',
            'event_type',
            'id',
            'lead_team',
            'location_type',
            'name',
            'notes',
            'organiser',
            'has_related_trade_agreements',
            'related_trade_agreements',
            'related_programmes',
            'start_date',
            'teams',
            'service',
            'uk_region',
        )
        read_only_fields = (
            'archived_documents_url_path',
            'disabled_on',
        )
