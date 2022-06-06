from datahub.activity_stream.serializers import ActivitySerializer
from datahub.event.models import Event


class EventActivitySerializer(ActivitySerializer):
    """Event serialiser for activity stream."""

    class Meta:
        model = Event

    def to_representation(self, instance):
        event_id = f'dit:DataHubEvent:{instance.pk}'
        event = {
            'id': f'{event_id}:Announce',
            'type': 'Announce',
            'published': instance.created_on,
            'generator': self._get_generator(),
            'object': {
                'id': event_id,
                'type': 'dit:Event',
                'name': instance.name,
                'dit:eventType': {'name': instance.event_type.name},
                'content': instance.notes,
                'startTime': instance.start_date,
                'endTime': instance.end_date,
                'url': instance.get_absolute_url(),
                'dit:locationType': {'name': instance.location_type.name},
                'dit:address_1': instance.address_1,
                'dit:address_2': instance.address_2,
                'dit:address_town': instance.address_town,
                'dit:address_county': instance.address_county,
                'dit:address_postcode': instance.address_postcode,
                'dit:address_country': {'name': instance.address_country.name},
                'dit:leadTeam': {'name': instance.lead_team.name},
                'dit:organiser': {'name': instance.organiser.name},
                'dit:disabledOn': instance.disabled_on,
                'dit:service': {'name': instance.service.name},
                'dit:archivedDocumentsUrlPath': instance.archived_documents_url_path,              

            },

        }
        if instance.uk_region is not None:
            event['object']['dit:ukRegion'] = {
                'name': instance.uk_region.name,
            }

        return event
