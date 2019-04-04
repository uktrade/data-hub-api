import base64
from logging import getLogger

import icalendar
import pytz
from django.db import transaction

from datahub.company.models.adviser import Advisor
from datahub.company.models.contact import Contact
from datahub.email_ingestion.email_processor import EmailProcessor
from datahub.email_ingestion.validation import email_sent_by_dit
from datahub.interaction.models import Interaction, InteractionDITParticipant


logger = getLogger(__name__)


class CalendarInteractionEmailProcessor(EmailProcessor):
    """
    An EmailProcessor which checks whether incoming email is a valid DIT/company
    meeting and creates an incomplete Interaction model for it if so.
    """

    def _get_adviser_for_email(self, email):
        try:
            return Advisor.objects.get(email=email)
        except Advisor.DoesNotExist:
            return None

    def _get_company_from_contacts(self, contacts):
        # TODO: Make this a better guess
        return contacts[0].company

    def _grab_calendar_string_from_text(self, message):
        for text_part in message.text_plain:
            if text_part.startswith('BEGIN:VCALENDAR'):
                return text_part
        return False

    def _grab_calendar_string_from_attachments(self, message):
        for attachment in message.attachments:
            if attachment['mail_content_type'] == 'application/ics':
                encoded_cal_text = base64.b64decode(attachment['payload'])
                return encoded_cal_text.decode('utf-8', 'ignore')
        return False

    def _get_utc_datetime(self, localised_datetime):
        try:
            return localised_datetime.astimezone(pytz.utc)
        except AttributeError:
            return localised_datetime

    def _get_calendar_event_metadata(self, message):
        calendar_string = self._grab_calendar_string_from_text(message)
        if not calendar_string:
            calendar_string = self._grab_calendar_string_from_attachments(message)
        if not calendar_string:
            return False
        calendar = icalendar.Calendar.from_ical(calendar_string)
        # TODO: Review how naive this approach is - what if an adviser sent their
        # whole calendar to datahub for whatever reason..?
        for component in calendar.walk():
            if component.name == 'VEVENT':
                return {
                    'subject': str(component.get('summary')),
                    'start': self._get_utc_datetime(component.decoded('dtstart')),
                    'end': self._get_utc_datetime(component.decoded('dtend')),
                    'sent': self._get_utc_datetime(component.decoded('dtstamp')),
                    'location': str(component.get('location')),
                    'status': str(component.get('status')),
                    'uid': str(component.get('uid')),
                }
        return False

    @transaction.atomic
    def _build_incomplete_interaction(
        self,
        sender_adviser,
        secondary_advisers,
        contacts,
        company,
        calendar_event,
    ):
        # TODO: Sort out signature of this method
        # TODO: Evaluate whether this method needs to be moved in to the modelling
        # layer
        interaction = Interaction.objects.create(
            kind=Interaction.KINDS.interaction,
            state=Interaction.STATES.incomplete,
            location=calendar_event['location'],
            meeting_uid=calendar_event['uid'],
            date=calendar_event['start'],
            company=company,
            contact=contacts[0],
            subject=calendar_event['subject'],  # This should be auto-generated
            dit_adviser=sender_adviser,
            dit_team=sender_adviser.dit_team,
            was_policy_feedback_provided=False,
        )
        for contact in contacts:
            interaction.contacts.add(contact)
        interaction.save()
        all_advisers = [sender_adviser]
        all_advisers.extend(secondary_advisers)
        for adviser in all_advisers:
            InteractionDITParticipant.objects.create(
                interaction=interaction,
                adviser=adviser,
                team=adviser.dit_team,
            )
        return interaction

    def process_email(self, message):
        """
        Review the metadata and calendar attachment (if present) of an email
        message to see if it fits the our criteria of a valid Data Hub meeting
        reqquest.  If it does, create an incomplete Interaction for it.

        Args:
          * ``message`` - mailparser.MailParser object - the message to process
        """
        if not email_sent_by_dit(message):
            return (False, 'Email not sent by DIT')
        sender_email = message.from_[0][1]
        sender_adviser = self._get_adviser_for_email(sender_email)
        if not sender_adviser:
            return (False, 'Email not sent by recognised DIT Adviser')
        all_recipients = [item[1].strip() for item in message.to]
        all_recipients.extend([item[1].strip() for item in message.cc])
        all_recipients = set(all_recipients)
        contacts = Contact.objects.filter(email__in=all_recipients)
        secondary_advisers = Advisor.objects\
            .filter(email__in=all_recipients)\
            .exclude(id=sender_adviser.id)
        if not contacts.count() > 0:
            return (False, 'No email receipients were recognised as Contacts')
        company = self._get_company_from_contacts(contacts)
        calendar_event = self._get_calendar_event_metadata(message)
        logger.info(calendar_event)
        if not calendar_event:
            return (False, 'No calendar event could be extracted')
        meeting_confirmed = calendar_event['status'] == 'CONFIRMED'
        if not meeting_confirmed:
            return (False, 'Calendar event was not status: CONFIRMED')
        matching_interactions = Interaction.objects.filter(meeting_uid=calendar_event['uid'])
        meeting_exists = matching_interactions.count() > 0
        # For our initial iteration, we are ignoring meeting updates
        if meeting_exists:
            return (False, 'Meeting already exists as an interaction')
        # We've validated and marshalled everything we need to build an
        # incomplete interaction
        interaction = self._build_incomplete_interaction(
            sender_adviser=sender_adviser,
            secondary_advisers=secondary_advisers,
            contacts=contacts,
            company=company,
            calendar_event=calendar_event,
        )
        return (True, 'Successfully created interaction #%s' % interaction.id)
