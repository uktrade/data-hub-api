import base64
import datetime
from collections import Counter

import icalendar
from django.core.exceptions import ValidationError
from django.utils.timezone import utc

from datahub.company.contact_matching import (
    find_active_contact_by_email_address,
    MatchStrategy,
)
from datahub.email_ingestion.validation import was_email_sent_by_dit
from datahub.interaction.email_processors.utils import (
    get_all_recipients,
    get_best_match_adviser_by_email,
)


ICALENDAR_CONTENT_TYPE = 'application/ics'
BEGIN_VCALENDAR = 'BEGIN:VCALENDAR'
CALENDAR_STATUS_CONFIRMED = 'CONFIRMED'
CALENDAR_COMPONENT_VEVENT = 'VEVENT'

USER_READABLE_ERROR_MESSAGES = {
    'no_contacts': (
        'The calendar invitation you sent to Data Hub did not include an email address '
        'that is recognised as a contact on Data Hub. The invitation must also be sent '
        'to Data Hub at the same time (and not forwarded to Data Hub later). Please '
        'check both of these things when resending your invitation and if you still '
        'see this message after resending the invitation, contact the Data Hub support '
        'team.',
    ),
    'bad_calendar_format': (
        'It looks like you sent something to Data Hub that was not a calendar invitation. '
        'Please send to Data Hub a calendar invitation (not an email or another type of '
        'message). If you still see this error message after sending a calendar email, '
        'please contact the Data Hub support team.',
    ),
}


def _get_top_company_from_contacts(contacts):
    """
    Get the company from the given contacts.
    If these contacts are related to different companies, return the company
    with the highest number of contacts in our iterable.
    """
    company_counts = Counter(contact.company for contact in contacts)
    top_company, _ = company_counts.most_common(1)[0]
    return top_company


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


def _convert_calendar_time_to_utc_datetime(calendar_time):
    """
    Takes a scheduled calendar time (could be a datetime.date or datetime.datetime)
    and transposes it to a UTC datetime.
    """
    # If calendar_time is a datetime.date, make it a datetime
    if not isinstance(calendar_time, datetime.datetime):
        calendar_time = datetime.datetime(
            day=calendar_time.day,
            month=calendar_time.month,
            year=calendar_time.year,
        )
    # If calendar_time does not have a timezone, this will assume calendar_time
    # is the default timezone for this django project
    return calendar_time.astimezone(utc)


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
            log_message = 'Email was malformed - missing "from" header'
            raise ValidationError(log_message)
        if not was_email_sent_by_dit(self.message):
            log_message = (
                'The meeting email did not pass our minimal checks to be verified as '
                'having been sent by a valid DIT Adviser email domain.'
            )
            raise ValidationError(log_message)
        sender_adviser = get_best_match_adviser_by_email(sender_email)
        if not sender_adviser:
            log_message = 'Email not sent by recognised DIT Adviser'
            raise ValidationError(log_message)
        return sender_adviser

    def _extract_and_validate_contacts(self, all_recipients):
        contacts = []
        for recipient_email in all_recipients:
            contact, _ = find_active_contact_by_email_address(
                recipient_email,
                MatchStrategy.MAX_INTERACTIONS,
            )
            if contact:
                contacts.append(contact)
        if not contacts:
            log_message = (
                'The meeting email had no recipients which were recognised as Data Hub '
                'contacts.'
            )
            raise ValidationError(USER_READABLE_ERROR_MESSAGES['no_contacts'])
        return contacts

    def _extract_secondary_advisers(self, all_recipients, sender_adviser):
        """
        Extract the secondary (non-sender) advisers for the calendar invite - that is,
        any advisers that received the invite who did not send it.
        """
        secondary_advisers = []
        for recipient_email in all_recipients:
            adviser = get_best_match_adviser_by_email(recipient_email)
            if adviser and adviser != sender_adviser:
                secondary_advisers.append(adviser)
        return secondary_advisers

    def _extract_and_validate_calendar_event_component(self):
        error = ValidationError(USER_READABLE_ERROR_MESSAGES['bad_calendar_format'])
        calendar_string = _extract_calendar_string_from_text(self.message)
        if not calendar_string:
            calendar_string = _extract_calendar_string_from_attachments(self.message)
        if not calendar_string:
            log_message = "There was no calendar attachment on the email"
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
            log_message = 'No calendar event was found in the iCalendar attachment.'
            raise error
        if len(calendar_event_components) > 1:
            log_message = (
                f'There were {len(calendar_event_components)} events in the calendar '
                '- expected 1 event in the iCalendar attachment.'
            )
            raise error
        return calendar_event_components[0]

    def _extract_and_validate_calendar_event_metadata(self):
        event_component = self._extract_and_validate_calendar_event_component()
        location = str(event_component.get('location') or '')
        calendar_event = {
            'subject': str(event_component.get('summary')),
            'start': _convert_calendar_time_to_utc_datetime(event_component.decoded('dtstart')),
            'end': _convert_calendar_time_to_utc_datetime(event_component.decoded('dtend')),
            'sent': _convert_calendar_time_to_utc_datetime(event_component.decoded('dtstamp')),
            'location': location,
            'status': str(event_component.get('status')),
            'uid': str(event_component.get('uid')),
        }

        meeting_confirmed = calendar_event['status'] == CALENDAR_STATUS_CONFIRMED
        if not meeting_confirmed:
            log_message = f'The calendar event was not status: {CALENDAR_STATUS_CONFIRMED}.',
            raise ValidationError(USER_READABLE_ERROR_MESSAGES['bad_calendar_format'])

        return calendar_event

    def extract_interaction_data_from_email(self):
        """
        Extract interaction data from the email message as a dictionary.

        This raises a ValidationError if the interaction data could not be fully extracted
        or is invalid according to business logic.
        """
        calendar_event = self._extract_and_validate_calendar_event_metadata()
        all_recipients = get_all_recipients(self.message)
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
