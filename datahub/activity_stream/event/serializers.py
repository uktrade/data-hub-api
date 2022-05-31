from datahub.activity_stream.serializers import ActivitySerializer
from datahub.event.models import Event


class EventActivitySerializer(ActivitySerializer):
    """Event serialiser for activity stream."""

    class Meta:
        model = Event

    def get_event_context(self, event):
        return {} if event is None else {
            id: f'dit:DataHubEvent:{event.pk}'
        }

    def to_representation(self, instance):
        event_id = f'dit:DataHubEvent:{instance.pk}'
        event = {
            'id': f'{event_id}:Announce',
            'type': 'Announce',
            'published': instance.created_on,
            'generator': self._get_generator(),
            'object': {
                'id': event_id,
                'type': instance.event_type,
                'content': instance.notes,
                'startTime': instance.start_date,
                'url': instance.get_absolute_url(),
                'dit:locationType': instance.location_type,
                'dit:address_1': instance.address_1,
                'dit:address_2': instance.address_2,
                'dit:address_town': instance.address_town,
                'dit:address_county': instance.address_county,
                'dit:address_postcode': instance.address_postcode,
                'dit:address_country': instance.address_country,
                'dit:ukRegion': instance.uk_region,
                'dit:leadTeam': instance.lead_team,
                'dit:organiser': instance.organiser,
                'dit:teams': instance.teams,
                'dit:relatedProgrammes': instance.related_programmes,  # TODO: these might be arrays?
                'dit:relatedTradeAgreements': instance.related_trade_agreements,
                'dit:service': instance.service,
                'dit:archivedDocumentsUrlPath': instance.archived_documents_url_path,
                'dit:disabledOn': instance.disabled_on
            },
        }

        return event
