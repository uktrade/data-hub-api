import os
import pytz
import pytest
from datetime import datetime

import mailparser

from datahub.interaction.email_processors import CalendarInteractionEmailProcessor


class TestCalendarInteractionEmailProcessor:

    def get_processor(self):
        return CalendarInteractionEmailProcessor()

    @pytest.mark.parametrize(
        'email_file,expected_event_details',
        (
            (
                "email_samples/meeting_updates/outlook_online/initial.eml",
                {
                    "subject": "test meet",
                    "start": datetime(2019, 3, 29, 12, 0, tzinfo=pytz.utc),
                    "end": datetime(2019, 3, 29, 12, 30, tzinfo=pytz.utc),
                    "sent": datetime(2019, 3, 29, 11, 28, 24, tzinfo=pytz.utc),
                    "location": (
                        "SOMEWHERE Agency (10 Tunstall Studios, 34-44 "
                        "Tunstall Road, 10/11 Tunstall Studios, London, "
                        "England, United Kingdom)"
                    ),
                    "status": "CONFIRMED",
                    "uid": (
                        "040000008200E00074C5B7101A82E008000000001670528522E6D4"
                        "0100000000000000001000000079ABFE8513989A49988F0CF2BF5B0F5A"
                    ),
                }
            ),
            (
                "email_samples/meeting_updates/outlook_online/update.eml",
                {
                    "subject": "test meetz",
                    "start": datetime(2019, 3, 29, 12, 0, tzinfo=pytz.utc),
                    "end": datetime(2019, 3, 29, 12, 30, tzinfo=pytz.utc),
                    "sent": datetime(2019, 3, 29, 11, 28, 53, tzinfo=pytz.utc),
                    "location": (
                        "SOMEWHERE Agency (10 Tunstall Studios, 34-44 "
                        "Tunstall Road, 10/11 Tunstall Studios, London, "
                        "England, United Kingdom)"
                    ),
                    "status": "CONFIRMED",
                    "uid": (
                        "040000008200E00074C5B7101A82E008000000001670528522E6D4"
                        "0100000000000000001000000079ABFE8513989A49988F0CF2BF5B0F5A"
                    ),
                }
            ),
            (
                "email_samples/meeting_updates/gmail/initial.eml",
                {
                    "subject": "initial",
                    "start": datetime(2019, 3, 29, 16, 30, tzinfo=pytz.utc),
                    "end": datetime(2019, 3, 29, 17, 30, tzinfo=pytz.utc),
                    "sent": datetime(2019, 3, 29, 11, 36, 33, tzinfo=pytz.utc),
                    "location": (
                        "Somewhere, Unit FF - 305 - شارع المركز المالي - دبي - "
                        "United Arab Emirates"
                    ),
                    "status": "CONFIRMED",
                    "uid": "5iggr1e2luglss6c789b0scvgr@google.com",
                }
            ),
            (
                "email_samples/meeting_updates/gmail/update.eml",
                {
                    "subject": "update",
                    "start": datetime(2019, 3, 29, 16, 30, tzinfo=pytz.utc),
                    "end": datetime(2019, 3, 29, 18, 0, tzinfo=pytz.utc),
                    "sent": datetime(2019, 3, 29, 11, 39, 15, tzinfo=pytz.utc),
                    "location": (
                        "Somewhere, Unit FF - 305 - شارع المركز المالي - دبي - "
                        "United Arab Emirates"
                    ),
                    "status": "CONFIRMED",
                    "uid": "5iggr1e2luglss6c789b0scvgr@google.com",
                }
            ),
        ),
    )
    def test_get_calendar_event_metadata(self, email_file, expected_event_details):
        """
        """
        processor = self.get_processor()
        email_file_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            email_file,
        )
        message = mailparser.parse_from_file(email_file_path)
        calendar_event = processor.get_calendar_event_metadata(message)
        assert(calendar_event == expected_event_details)
