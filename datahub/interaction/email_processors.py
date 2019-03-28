import icalendar
import base64

from django.db import transaction

from datahub.company.models.adviser import Advisor
from datahub.company.models.contact import Contact
from datahub.interaction.models import Interaction, InteractionDITParticipant
from datahub.email_ingestion.email_processor import EmailProcessor
from datahub.email_ingestion.validation import email_sent_by_dit


class CalendarInteractionEmailProcessor(EmailProcessor):

    def get_adviser_for_email(self, email):
        """
        """
        try:
            return Advisor.objects.get(email=email)
        except Advisor.DoesNotExist:
            return None

    def get_company_from_contacts(self, contacts):
        """
        """
        # TODO: Make this a better guess
        return contacts[0].company

    def _grab_calendar_string_from_text(self, message):
        for text_part in message.text_plain:
            if text_part.startswith("BEGIN:VCALENDAR"):
                return text_part
        return False

    def _grab_calendar_string_from_attachments(self, message):
        for attachment in message.attachments:
            if attachment['mail_content_type'] == "application/ics":
                encoded_cal_text = base64.b64decode(attachment['payload'])
                return encoded_cal_text.decode("utf-8", "ignore")
        return False

    def get_calendar_event_metadata(self, message):
        calendar_string = self._grab_calendar_string_from_text(message)
        if not calendar_string:
            calendar_string = self._grab_calendar_string_from_attachments(message)
        if not calendar_string:
            return False
        calendar = icalendar.Calendar.from_ical(calendar_string)
        for component in calendar.walk():
            if component.name == "VEVENT":
                return {
                    "subject": component.decoded('summary'),
                    "start": component.decoded('dtstart'),
                    "end": component.decoded('dtend'),
                    "organiser": component.decoded('organizer'),
                    "attendee": component.decoded('attendee'),
                    "sent": component.decoded('dtstamp'),
                    "location": component.decoded('location'),
                }
        return False

    @transaction.atomic
    def build_incomplete_interaction(self, sender_adviser, secondary_advisers, contacts, company, calendar_event):
        # TODO: Sort out signature of this method
        # TODO: Evaluate whether this needs to be moved in to the modelling 
        # layer
        interaction = Interaction.objects.create(
            kind=Interaction.KINDS.interaction,
            state=Interaction.STATES.incomplete,
            location=calendar_event['location'],
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
        if not email_sent_by_dit(message):
            return (False, "Email not sent by DIT")
        sender_email = message.from_[0][1]
        sender_adviser = self.get_adviser_for_email(sender_email)
        if not sender_adviser:
            return (False, "Email not sent by recognised DIT Adviser")

        all_recipients = [item[1] for item in message.to]
        all_recipients.extend([item[1] for item in message.cc])
        all_recipients = set(all_recipients)
        contacts = Contact.objects.filter(email__in=all_recipients)
        secondary_advisers = Advisor.objects\
            .filter(email__in=all_recipients)\
            .exclude(id=sender_adviser.id)
        if not contacts.count() > 0:
            return (False, "No email receipients were recognised as Contacts")
        company = self.get_company_from_contacts(contacts)
        calendar_event = self.get_calendar_event_metadata(message)
        if not calendar_event:
            return (False, "No calendar event could be extracted")
        # We've validated and marshalled everything we need to build an 
        # interaction
        interaction = self.build_incomplete_interaction(
            sender_adviser=sender_adviser,
            secondary_advisers=secondary_advisers,
            contacts=contacts,
            company=company,
            calendar_event=calendar_event
        )
        return (True, "Successfully created interaction #%s" % interaction.id)
