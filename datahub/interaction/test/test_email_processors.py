import os
import pytest

from django.conf import settings
import mailparser

from datahub.interaction.email_processors import CalendarInteractionEmailProcessor

class TestCalendarInteractionEmailProcessor:

    def get_processor(self):
        return CalendarInteractionEmailProcessor()
        
    #@pytest.mark.parametrize(
    #    'email_file,expected_event_details'
    #    (
    #        (
    #            "email_samples/meeting_updates/gmail/outlook_online/initial.eml",
    #            {
    #                "subject": "initial",
    #                "start": "",
    #                "end": "",
    #                "organiser": "",
    #                "attendee": "",
    #                "sent": "",
    #                "location": "",
    #                "status": "CONFIRMED",
    #                "uid": "",
    #            }
    #        ),
    #        (
    #            "email_samples/meeting_updates/gmail/outlook_online/update.eml",
    #            {
    #                "subject": "update",
    #                "start": "",
    #                "end": "",
    #                "organiser": "",
    #                "attendee": "",
    #                "sent": "",
    #                "location": "",
    #                "status": "CONFIRMED",
    #                "uid": "",
    #            }
    #        ),
    #    ),
    #)
    @pytest.mark.parametrize(
        'email_file,expected_event_details',
        (
            (
                "email_samples/meeting_updates/outlook_online/initial.eml", 
                {
                    "subject": "initial",
                    "start": "",
                    "end": "",
                    "organiser": "",
                    "attendee": "",
                    "sent": "",
                    "location": "",
                    "status": "CONFIRMED",
                    "uid": "",
                }
            ),
            (
                "email_samples/meeting_updates/outlook_online/update.eml", 
                {
                    "subject": "initial",
                    "start": "",
                    "end": "",
                    "organiser": "",
                    "attendee": "",
                    "sent": "",
                    "location": "",
                    "status": "CONFIRMED",
                    "uid": "",
                }
            ),
        ),
    )
    def test_get_calendar_event_metadata(self, email_file, expected_event_details):
        """
        """
        print("X-MICROSOFT-CDO-OWNERAPPTID:2117332246")
        processor = self.get_processor()
        email_file_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            email_file,
        )
        message = mailparser.parse_from_file(email_file_path)
        calendar_event = processor.get_calendar_event_metadata(message)
        assert(calendar_event==expected_event_details)
