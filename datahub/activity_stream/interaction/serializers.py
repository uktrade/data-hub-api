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
        return {} if project is None else {
            'id': f'dit:DataHubInvestmentProject:{project.pk}',
            'type': 'dit:InvestmentProject',
            'name': project.name,
            'url': project.get_absolute_url(),
        }

    def _get_event_context(self, event):
        return {} if event is None else {
            'id': f'dit:DataHubEvent:{event.pk}',
            'type': 'dit:Event',
            'dit:eventType': {'name': event.event_type.name},
            'name': event.name,
            'startTime': event.start_date,
            'endTime': event.end_date,
            'dit:team': self._get_team(event.lead_team),
            'url': event.get_absolute_url(),
        }

    def _get_context(self, instance):
        if instance.kind == Interaction.Kind.INTERACTION:
            context = self._get_project_context(instance.investment_project)
        elif instance.kind == Interaction.Kind.SERVICE_DELIVERY:
            context = self._get_event_context(instance.event)
        else:
            context = {}
        return context

    def _get_adviser_with_team(self, participant):
        adviser = self._get_adviser(participant.adviser)
        if participant.team is not None:
            adviser['dit:team'] = self._get_team(participant.team)
        return adviser

    def _get_dit_participants(self, participants):
        return [
            self._get_adviser_with_team(participant)
            for participant in participants.all()
            if participant.adviser is not None
        ]

    def _get_team(self, team):
        return {} if team is None else {
            'id': f'dit:DataHubTeam:{team.pk}',
            'type': ['Group', 'dit:Team'],
            'name': team.name,
        }

    def to_representation(self, instance):
        """
        Serialize the interaction as per Activity Stream spec:
        https://www.w3.org/TR/activitystreams-core/
        """
        interaction_id = f'dit:DataHubInteraction:{instance.pk}'
        interaction = {
            'id': f'{interaction_id}:Announce',
            'type': 'Announce',
            'published': instance.created_on,
            'generator': self._get_generator(),
            'object': {
                'id': interaction_id,
                'type': ['dit:Event', f'dit:{self.KINDS_JSON[instance.kind]}'],
                'startTime': instance.date,
                'dit:status': instance.status,
                'dit:archived': instance.archived,
                'dit:subject': instance.subject,
                'attributedTo': [
                    self._get_company(instance.company),
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

        return interaction
