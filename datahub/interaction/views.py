import mailparser
from django_filters.rest_framework import DjangoFilterBackend
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import serializers
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.interaction.email_processors.exceptions import InvalidInviteError
from datahub.interaction.email_processors.parsers import CalendarInteractionEmailParser
from datahub.interaction.email_processors.processors import (
    _filter_contacts_to_single_company,
    _get_meeting_subject,
    CalendarInteractionEmailProcessor,
)
from datahub.interaction.models import Interaction
from datahub.interaction.permissions import (
    InteractionModelPermissions,
    IsAssociatedToInvestmentProjectInteractionFilter,
    IsAssociatedToInvestmentProjectInteractionPermission,
)
from datahub.interaction.queryset import get_interaction_queryset
from datahub.interaction.serializers import InteractionSerializer
from datahub.oauth.scopes import Scope


class InteractionViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Interaction ViewSet v3."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        InteractionModelPermissions,
        IsAssociatedToInvestmentProjectInteractionPermission,
    )
    serializer_class = InteractionSerializer
    queryset = get_interaction_queryset()
    filter_backends = (
        DjangoFilterBackend,
        IsAssociatedToInvestmentProjectInteractionFilter,
        OrderingFilter,
    )
    filterset_fields = [
        'company_id',
        'contacts__id',
        'event_id',
        'investment_project_id',
    ]
    ordering_fields = (
        'company__name',
        'created_on',
        'date',
        'first_name_of_first_contact',
        'last_name_of_first_contact',
        'subject',
    )
    ordering = ('-date', '-created_on')


class NoSaveProcessor(CalendarInteractionEmailProcessor):
    """
    Does exactly what the parent class does except for saving an
    interaction.
    """

    def _get_interaction_dict(self, data):
        return {
            'company': str(data['company'].id),
            'contacts': [str(contact.id) for contact in data['contacts']],
            'date': data['date'].isoformat(),
            'dit_participants': [
                str(participant['adviser'].id)
                for participant in data['dit_participants']
            ],
            'kind': data['kind'],
            'status': data['status'],
            'subject': data['subject'],
            'was_policy_feedback_provided': data['was_policy_feedback_provided'],
        }

    def process_email(self, message):
        """
        Review the metadata and calendar attachment (if present) of an email
        message to see if it fits the our criteria of a valid Data Hub meeting
        request.  If it does, return a serialised representation.
        """
        try:
            email_parser = CalendarInteractionEmailParser(message)
            interaction_data = email_parser.extract_interaction_data_from_email()
        except InvalidInviteError as exc:
            raise serializers.ValidationError(str(exc))

        # Make the same-company check easy to remove later if we allow Interactions
        # to have contacts from more than one company
        sanitised_contacts = _filter_contacts_to_single_company(
            interaction_data['contacts'],
            interaction_data['top_company'],
        )
        interaction_data['contacts'] = sanitised_contacts

        # Replace the meeting invite subject with one which details the people attending
        interaction_data['subject'] = _get_meeting_subject(
            interaction_data['sender'],
            interaction_data['contacts'],
            interaction_data['secondary_advisers'],
        )

        # Get a serializer for the interaction data
        serialiser = self.validate_with_serializer(interaction_data)

        # For our initial iteration of this feature, we are ignoring meeting updates
        matching_interactions = Interaction.objects.filter(
            source__contains={'meeting': {'id': interaction_data['meeting_details']['uid']}},
        )
        if matching_interactions.exists():
            raise serializers.ValidationError('Interaction already exists.')

        return self._get_interaction_dict(serialiser.validated_data)


class MailViewSet(APIView):
    """
    Takes a mail body and return parsed content.
    """

    permission_classes = (
        AllowAny,
    )

    def get(self, request):
        """
        Receive an .ical file, parse it and return the
        parsed content in the response.
        """
        message = mailparser.parse_from_string(request.query_params.get('message'))
        data = NoSaveProcessor().process_email(message)
        return Response(data)
