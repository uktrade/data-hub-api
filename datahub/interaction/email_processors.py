import base64
from collections import Counter
from logging import getLogger

import icalendar
from django.core.exceptions import ValidationError
from django.utils.timezone import utc
from rest_framework.exceptions import ValidationError as RestValidationError

from datahub.company.contact_matching import find_active_contact_by_email_address
from datahub.company.models.adviser import Advisor
from datahub.email_ingestion.email_processor import EmailProcessor
from datahub.email_ingestion.validation import was_email_sent_by_dit
from datahub.interaction.models import Interaction
from datahub.interaction.serializers import InteractionSerializer


logger = getLogger(__name__)

ICALENDAR_CONTENT_TYPE = 'application/ics'
BEGIN_VCALENDAR = 'BEGIN:VCALENDAR'
CALENDAR_STATUS_CONFIRMED = 'CONFIRMED'
CALENDAR_COMPONENT_VEVENT = 'VEVENT'


def _get_all_recipients(message):
    """
    Get all of the recipient emails from a MailParser message object.

    :returns: a set of all recipient emails
    """
    return {email.strip() for name, email in (*message.to, *message.cc)}


def _get_top_company_from_contacts(contacts):
    """
    Get the company from the given contacts.
    If these contacts are related to different companies, return the company
    with the highest number of contacts in our iterable.
    """
    company_counts = Counter(contact.company for contact in contacts)
    top_company, _ = company_counts.most_common(1)[0]
    return top_company


def _get_best_match_adviser_by_email(email):
    """
    Get the best-guess matching active adviser for a particular correspondence email
    address.

    This firstly attempts to get the oldest Advisor object with a matching
    `contact_email`, it will then attempt to match on `email`.  We prefer
    `contact_email` over `email` as this should most closely match the correspondence
    email address - the context here is that we are dealing with the email
    accounts that advisers use for setting up meetings/emailing companies.

    :param email: string email address
    :returns: an Advisor object or None, if a match could not be found
    """
    for field in ['contact_email', 'email']:
        criteria = {field: email, 'is_active': True}
        try:
            return Advisor.objects.filter(**criteria).earliest('date_joined')
        except Advisor.DoesNotExist:
            continue
    return None


def _extract_calendar_string_from_text(message):
    """
    Extract an icalendar string from the plain text of a message.

    :param message: MailParser message object
    :returns: A string of the icalendar body or None if it could not be found in plain text
    """
    for text_part in message.text_plain:
        if text_part.startswith(BEGIN_VCALENDAR):
            return text_part
    return None


def _extract_calendar_string_from_attachments(message):
    """
    Extract an icalendar string from the attachements of a message.

    :param message: MailParser message object
    :returns: A string of the icalendar body or None if no ICS file could be found in
        the message's attachments
    """
    for attachment in message.attachments:
        if attachment['mail_content_type'] == ICALENDAR_CONTENT_TYPE:
            encoded_cal_text = base64.b64decode(attachment['payload'])
            return encoded_cal_text.decode('utf-8', 'ignore')
    return None


def _get_utc_datetime(localised_datetime):
    try:
        return localised_datetime.astimezone(utc)
    # When the calendar event is just a date
    except AttributeError:
        return localised_datetime


class CalendarInteractionEmailProcessor(EmailProcessor):
    """
    An EmailProcessor which checks whether incoming email is a valid DIT/company
    meeting and creates an incomplete Interaction model for it if so.
    """

    def _transform(self, data):
        dit_participants = [
            {
                'adviser': {'id': adviser.id},
                'team': adviser.dit_team,
            }
            for adviser in (data['sender'], *data['secondary_advisers'])
        ]

        creation_data = {
            'contacts': [{'id': contact.id} for contact in data['contacts']],
            'company': {'id': data['company'].id},
            'date': data['date'],
            'dit_participants': dit_participants,
            'kind': Interaction.KINDS.interaction,
            'status': Interaction.STATUSES.draft,
            'subject': data['subject'],
            'location': data['location'],
            'was_policy_feedback_provided': False,
        }

        return creation_data

    def _reduce_contacts_to_single_company(self, interaction_data):
        contacts = interaction_data['contacts']
        company = interaction_data['company']
        interaction_data['contacts'] = [
            contact
            for contact in contacts
            if contact.company == company
        ]

    def validate_with_serializer(self, data):
        """
        Transforms extracted data into a dict suitable for use with InteractionSerializer
        and then runs data through this serializer for validation.

        Returns the instantiated serializer.
        """
        transformed_data = self._transform(data)
        serializer = InteractionSerializer(context={'is_bulk_import': True}, data=transformed_data)
        serializer.is_valid(raise_exception=True)
        return serializer

    def process_email(self, message):
        """
        Review the metadata and calendar attachment (if present) of an email
        message to see if it fits the our criteria of a valid Data Hub meeting
        request.  If it does, create an incomplete Interaction for it.

        :param message: mailparser.MailParser object - the message to process
        """
        email_parser = CalendarInteractionEmailParser(message)
        try:
            interaction_data = email_parser.extract_interaction_data_from_email(message)
        except ValidationError as exc:
            return (False, exc.message)
        self._reduce_contacts_to_single_company(interaction_data)
        try:
            serializer = self.validate_with_serializer(interaction_data)
        except RestValidationError as exc:
            error_parts = []
            for field_name, details in exc.detail.items():
                details_string = ','.join([str(detail) for detail in details])
                error_parts.append(f'{field_name}: {details_string}')
            return (False, '\n'.join(error_parts))
        # For our initial iteration, we are ignoring meeting updates
        matching_interactions = Interaction.objects.filter(
            source__id=interaction_data['meeting_details']['uid'],
            source__type=Interaction.SOURCE_TYPES.meeting,
        )
        if matching_interactions:
            return (False, 'Meeting already exists as an interaction')
        # We've validated and marshalled everything we need to build an
        # incomplete interaction
        interaction = serializer.save(
            source={
                'id': interaction_data['meeting_details']['uid'],
                'type': Interaction.SOURCE_TYPES.meeting,
            },
        )
        return (True, f'Successfully created interaction #{interaction.id}')


class CalendarInteractionEmailParser:
    """
    Parses and extracts calendar interaction information from a MailParser email
    object.
    """

    def __init__(self, message):
        """
        Initialise the CalendarInteractionEmailParser with a MailParser email
        object.
        """
        self.message = message

    def _extract_and_validate_sender_adviser(self):
        try:
            sender_email = self.message.from_[0][1]
        except IndexError:
            raise ValidationError('Email was malformed - missing "from" header')
        if not was_email_sent_by_dit(self.message):
            raise ValidationError('Email not sent by DIT')
        sender_adviser = _get_best_match_adviser_by_email(sender_email)
        if not sender_adviser:
            raise ValidationError('Email not sent by recognised DIT Adviser')
        return sender_adviser

    def _extract_and_validate_contacts(self, all_recipients):
        contacts = []
        for recipient_email in all_recipients:
            contact, _ = find_active_contact_by_email_address(recipient_email)
            if contact:
                contacts.append(contact)
        if not contacts:
            raise ValidationError('No email recipients were recognised as Contacts')
        return contacts

    def _extract_secondary_advisers(self, all_recipients, sender_adviser):
        """
        Extract the secondary (non-sender) advisers for the calendar invite - that is,
        any advisers that received the invite who did not send it.
        """
        secondary_advisers = []
        for recipient_email in all_recipients:
            adviser = _get_best_match_adviser_by_email(recipient_email)
            if adviser:
                secondary_advisers.append(adviser)
        return secondary_advisers

    def _extract_and_validate_calendar_event_component(self):
        error = ValidationError('No calendar event could be extracted')
        calendar_string = _extract_calendar_string_from_text(self.message)
        if not calendar_string:
            calendar_string = _extract_calendar_string_from_attachments(self.message)
        if not calendar_string:
            raise error
        try:
            calendar = icalendar.Calendar.from_ical(calendar_string)
        except ValueError as exc:
            raise error from exc
        calendar_event_components = [
            comp for comp in calendar.walk()
            if comp.name == CALENDAR_COMPONENT_VEVENT
        ]
        if len(calendar_event_components) == 0:
            raise ValidationError('No calendar event was found in the calendar')
        if len(calendar_event_components) > 1:
            raise ValidationError(
                f'There were {len(calendar_event_components)} events in the calendar '
                '- expected 1 event',
            )
        return calendar_event_components[0]

    def _extract_and_validate_calendar_event_metadata(self):
        event_component = self._extract_and_validate_calendar_event_component()
        location = str(event_component.get('location') or '')
        calendar_event = {
            'subject': str(event_component.get('summary')),
            'start': _get_utc_datetime(event_component.decoded('dtstart')),
            'end': _get_utc_datetime(event_component.decoded('dtend')),
            'sent': _get_utc_datetime(event_component.decoded('dtstamp')),
            'location': location,
            'status': str(event_component.get('status')),
            'uid': str(event_component.get('uid')),
        }

        meeting_confirmed = calendar_event['status'] == CALENDAR_STATUS_CONFIRMED
        if not meeting_confirmed:
            raise ValidationError(f'Calendar event was not status: {CALENDAR_STATUS_CONFIRMED}')

        return calendar_event

    def extract_interaction_data_from_email(self):
        """
        Extract interaction data from the email message as a dictionary.

        This raises a ValidationError if the interaction data could not be fully extracted
        or is invalid according to business logic.
        """
        calendar_event = self._extract_and_validate_calendar_event_metadata()
        all_recipients = _get_all_recipients(self.message)
        sender = self._extract_and_validate_sender_adviser()
        secondary_advisers = self._extract_secondary_advisers(all_recipients, sender)
        contacts = self._extract_and_validate_contacts(all_recipients)
        top_company = _get_top_company_from_contacts(contacts)

        return {
            'sender': sender,
            'contacts': contacts,
            'secondary_advisers': secondary_advisers,
            'top_company': top_company,
            'date': calendar_event['start'],
            'location': calendar_event['location'],
            'meeting_details': calendar_event,
            'subject': calendar_event['subject'],
        }
