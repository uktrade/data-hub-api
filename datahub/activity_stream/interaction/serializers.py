from datahub.activity_stream.serializers import ActivitySerializer
from datahub.interaction.models import Interaction


class InteractionActivitySerializer(ActivitySerializer):
    """Interaction serialiser for activity stream."""

    KINDS_JSON = {
        Interaction.Kind.INTERACTION: 'Interaction',
        Interaction.Kind.SERVICE_DELIVERY: 'ServiceDelivery',
    }

    class Meta:
        model = Interaction

    def _get_project_context(self, project):
        return (
            {}
            if project is None
            else {
                'id': f'dit:DataHubInvestmentProject:{project.pk}',
                'type': 'dit:InvestmentProject',
                'name': project.name,
                'url': project.get_absolute_url(),
            }
        )

    def _get_event_context(self, event):
        return (
            {}
            if event is None
            else {
                'id': f'dit:DataHubEvent:{event.pk}',
                'type': 'dit:Event',
                'dit:eventType': {'name': event.event_type.name},
                'name': event.name,
                'startTime': event.start_date,
                'endTime': event.end_date,
                'dit:team': self._get_team(event.lead_team),
                'url': event.get_absolute_url(),
            }
        )

    def _get_context(self, instance):
        if instance.kind == Interaction.Kind.INTERACTION:
            context = self._get_project_context(instance.investment_project)
        elif instance.kind == Interaction.Kind.SERVICE_DELIVERY:
            context = self._get_event_context(instance.event)
        else:
            context = {}
        return context

    def _get_dit_participants(self, participants):
        return [
            self._get_adviser_with_team(participant.adviser, participant.team)
            for participant in participants.all()
            if participant.adviser is not None
        ]

    def to_representation(self, instance):
        """Serialize the interaction as per Activity Stream spec:
        https://www.w3.org/TR/activitystreams-core/.
        """
        interaction_id = f'dit:DataHubInteraction:{instance.pk}'
        interaction = {
            'id': f'{interaction_id}:Announce',
            'type': 'Announce',
            'published': instance.created_on,
            'generator': self._get_generator(),
            'object': {
                'id': interaction_id,
                'type': [
                    'dit:Event',
                    f'dit:{self.KINDS_JSON[instance.kind]}',
                    f'dit:datahub:theme:{instance.theme}',
                ],
                'content': instance.notes,
                'startTime': instance.date,
                'dit:status': instance.status,
                'dit:archived': instance.archived,
                'dit:subject': instance.subject,
                'dit:business_intelligence': instance.was_policy_feedback_provided,
                'attributedTo': [
                    *self._get_companies(instance.companies),
                    *self._get_dit_participants(instance.dit_participants),
                    *self._get_contacts(instance.contacts),
                ],
                'url': instance.get_absolute_url(),
            },
        }

        context = self._get_context(instance)
        if context:
            interaction['object']['context'] = [context]

        if (
            instance.kind == Interaction.Kind.INTERACTION
            and instance.communication_channel is not None
        ):
            interaction['object']['dit:communicationChannel'] = {
                'name': instance.communication_channel.name,
            }

        if instance.service is not None:
            interaction['object']['dit:service'] = {
                'name': instance.service.name,
            }

        if instance.helped_remove_export_barrier:
            interaction['object']['dit:exportBarrierTypes'] = [
                {'name': barrier.name} for barrier in instance.export_barrier_types.all()
            ]
            if instance.export_barrier_notes != '':
                interaction['object']['dit:exportBarrierNotes'] = instance.export_barrier_notes

        return interaction
