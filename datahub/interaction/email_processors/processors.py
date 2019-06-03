from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from datahub.email_ingestion.email_processor import EmailProcessor
from datahub.interaction.email_processors.parsers import CalendarInteractionEmailParser
from datahub.interaction.models import Interaction
from datahub.interaction.serializers import InteractionSerializer


def _flatten_serializer_errors_to_string(serializer_errors):
    """
    Flatten DRF Serializer validation errors to a string with one field per line.
    """
    error_parts = []
    for field_name, details in serializer_errors.items():
        details_string = ','.join([str(detail) for detail in details])
        error_parts.append(f'{field_name}: {details_string}')
    return '\n'.join(error_parts)


def _filter_contacts_to_single_company(contacts, company):
    """
    Given a list of contacts and a company, return all of the contacts who are
    attributed to that company.
    """
    return [contact for contact in contacts if contact.company == company]


def _get_meeting_subject(sender, contacts, secondary_advisers):
    """
    Construct and return a meeting subject given a sender, contacts and secondary
    advisers (if present).
    """
    adviser_names = [
        adviser.name
        for adviser in (sender, *secondary_advisers)
        if adviser.name
    ]
    if not adviser_names:
        adviser_names = ['DIT']
    contact_names = [contact.name for contact in contacts if contact.name]
    if not contact_names:
        try:
            contact_names = [contacts[0].company.name]
        except IndexError:
            # This is not going to be a valid interaction, but this helper function
            # should not raise an exception
            contact_names = ['a company']
    all_names = (*adviser_names, *contact_names)
    comma_names = ', '.join(all_names[:-1])
    return f'Meeting between {comma_names} and {all_names[-1]}'


class CalendarInteractionEmailProcessor(EmailProcessor):
    """
    An EmailProcessor which checks whether incoming email is a valid DIT/company
    meeting, parses meeting information and creates a draft Interaction model
    instance for it if the information is valid.
    """

    def _to_serializer_format(self, data):
        dit_participants = [
            {
                'adviser': {'id': adviser.id},
                'team': adviser.dit_team,
            }
            for adviser in (data['sender'], *data['secondary_advisers'])
        ]

        data_for_serializer = {
            'contacts': [{'id': contact.id} for contact in data['contacts']],
            'company': {'id': data['top_company'].id},
            'date': data['date'],
            'dit_participants': dit_participants,
            'kind': Interaction.KINDS.interaction,
            'status': Interaction.STATUSES.draft,
            'subject': data['subject'],
            'location': data['location'],
            'was_policy_feedback_provided': False,
        }

        return data_for_serializer

    def validate_with_serializer(self, data):
        """
        Transforms extracted data into a dict suitable for use with InteractionSerializer
        and then runs data through this serializer for validation.

        Returns the instantiated serializer.
        """
        transformed_data = self._to_serializer_format(data)
        serializer = InteractionSerializer(context={'is_bulk_import': True}, data=transformed_data)
        serializer.is_valid(raise_exception=True)
        return serializer

    @transaction.atomic
    def save_serializer_as_interaction(self, serializer, interaction_data):
        """
        Create the interaction model instance from the validated serializer.
        """
        # Provide an overridden value for source - so that we save the meeting
        # data properly
        interaction = serializer.save(
            source={
                'meeting': {'id': interaction_data['meeting_details']['uid']},
            },
        )
        return interaction

    def process_email(self, message):
        """
        Review the metadata and calendar attachment (if present) of an email
        message to see if it fits the our criteria of a valid Data Hub meeting
        request.  If it does, create a draft Interaction for it.

        :param message: mailparser.MailParser object - the message to process
        """
        # Parse the email for interaction data
        email_parser = CalendarInteractionEmailParser(message)
        try:
            interaction_data = email_parser.extract_interaction_data_from_email()
        except ValidationError as exc:
            return (False, exc.message)  # noqa: B306

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
        try:
            serializer = self.validate_with_serializer(interaction_data)
        except serializers.ValidationError as exc:
            return (False, _flatten_serializer_errors_to_string(exc.detail))

        # For our initial iteration of this feature, we are ignoring meeting updates
        matching_interactions = Interaction.objects.filter(
            source__contains={'meeting': {'id': interaction_data['meeting_details']['uid']}},
        )
        if matching_interactions.exists():
            return (False, 'Meeting already exists as an interaction')

        interaction = self.save_serializer_as_interaction(serializer, interaction_data)
        return (True, f'Successfully created interaction #{interaction.id}')
