import base64
from collections import Counter
from logging import getLogger

import icalendar
import pytz
from django.core.exceptions import ValidationError

from datahub.company.contact_adviser_matching import (
    find_active_adviser_by_email_address,
    find_active_contact_by_email_address,
)
from datahub.email_ingestion.validation import was_email_sent_by_dit


logger = getLogger(__name__)


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

    def _verify_email_sent_by_dit(self):
        if not was_email_sent_by_dit(self.message):
            raise ValidationError('Email not sent by DIT')

    def _extract_sender_adviser(self):
        sender_email = self.message.from_[0][1]
        sender_adviser, matching_status = find_active_adviser_by_email_address(sender_email)
        if not sender_adviser:
            raise ValidationError('Email not sent by recognised DIT Adviser')
        return sender_adviser

    def _get_all_recipients(self):
        all_recipients = set()
        for recipients in [self.message.to, self.message.cc]:
            all_recipients = all_recipients.union(
                {recipient[1].strip() for recipient in recipients},
            )
        return all_recipients

    def _extract_contacts(self, all_recipients):
        contacts = []
        for recipient_email in all_recipients:
            contact, matching_status = find_active_contact_by_email_address(recipient_email)
            if contact:
                contacts.append(contact)
        if not contacts:
            raise ValidationError('No email recipients were recognised as Contacts')
        return contacts

    def _extract_secondary_advisers(self, all_recipients, sender_adviser):
        secondary_advisers = []
        for recipient_email in all_recipients:
            adviser, matching_status = find_active_adviser_by_email_address(recipient_email)
            if adviser:
                secondary_advisers.append(adviser)
        return secondary_advisers

    def _get_company_from_contacts(self, contacts):
        """
        Get the company from the given contacts.
        If these contacts are related to different companies, return the company
        with the highest number of contacts in our iterable.
        """
        company_counts = Counter([contact.company for contact in contacts])
        top_company = company_counts.most_common()[0]
        return top_company

    def _grab_calendar_string_from_text(self):
        for text_part in self.message.text_plain:
            if text_part.startswith('BEGIN:VCALENDAR'):
                return text_part
        return False

    def _grab_calendar_string_from_attachments(self):
        for attachment in self.message.attachments:
            if attachment['mail_content_type'] == 'application/ics':
                encoded_cal_text = base64.b64decode(attachment['payload'])
                return encoded_cal_text.decode('utf-8', 'ignore')
        return False

    def _get_utc_datetime(self, localised_datetime):
        try:
            return localised_datetime.astimezone(pytz.utc)
        # When the calendar event is just a date
        except AttributeError:
            return localised_datetime

    def _get_calendar_event_component(self):
        error = ValidationError('No calendar event could be extracted')
        calendar_string = self._grab_calendar_string_from_text()
        if not calendar_string:
            calendar_string = self._grab_calendar_string_from_attachments()
        if not calendar_string:
            raise error
        try:
            calendar = icalendar.Calendar.from_ical(calendar_string)
        except Exception as exc:
            raise error from exc
        calendar_event_components = []
        for component in calendar.walk():
            if component.name == 'VEVENT':
                calendar_event_components.append(component)
        if len(calendar_event_components) == 0:
            raise ValidationError('No calendar event was found in the calendar')
        if len(calendar_event_components) > 1:
            raise ValidationError(
                f'There were {len(calendar_event_components)} events in the calendar '
                '- expected 1 event',
            )
        return calendar_event_components[0]

    def _get_calendar_event_metadata(self):
        event_component = self._get_calendar_event_component()
        location = event_component.get('location')
        if location:
            location = str(location)
        else:
            location = ''
        return {
            'subject': str(event_component.get('summary')),
            'start': self._get_utc_datetime(event_component.decoded('dtstart')),
            'end': self._get_utc_datetime(event_component.decoded('dtend')),
            'sent': self._get_utc_datetime(event_component.decoded('dtstamp')),
            'location': location,
            'status': str(event_component.get('status')),
            'uid': str(event_component.get('uid')),
        }

    def extract_interaction_data_from_email(self):
        """
        Extract interaction data from the email message as a dictionary.

        This raises a ValidationError if the interaction data could not be fully extracted
        or is invalid according to business logic.
        """
        interaction_data = {}
        self._verify_email_sent_by_dit()
        interaction_data['sender'] = self._extract_sender_adviser()
        all_recipients = self._get_all_recipients()
        interaction_data['contacts'] = self._extract_contacts(all_recipients)
        interaction_data['secondary_advisers'] = self._extract_secondary_advisers(
            all_recipients,
            interaction_data['sender'],
        )
        interaction_data['company'] = self._get_company_from_contacts(interaction_data['contacts'])
        calendar_event = self._get_calendar_event_metadata()
        interaction_data['date'] = calendar_event['start']
        interaction_data['location'] = calendar_event['location']
        interaction_data['meeting_details'] = calendar_event
        interaction_data['subject'] = calendar_event['subject']
        meeting_confirmed = calendar_event['status'] == 'CONFIRMED'
        if not meeting_confirmed:
            raise ValidationError('Calendar event was not status: CONFIRMED')
        return interaction_data
