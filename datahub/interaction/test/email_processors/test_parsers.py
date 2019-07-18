from datetime import datetime
from pathlib import PurePath

import mailparser
import pytest
from django.core.exceptions import ValidationError
from django.utils.timezone import utc

from datahub.interaction.email_processors.parsers import CalendarInteractionEmailParser


@pytest.mark.django_db
class TestCalendarInteractionEmailParser:
    """
    Test the CalendarInteractionEmailParser class.
    """

    def _get_parser_for_email_file(self, relative_email_file_path):
        email_file_path = PurePath(__file__).parent / relative_email_file_path
        message = mailparser.parse_from_file(email_file_path)
        return CalendarInteractionEmailParser(message)

    @pytest.mark.parametrize(
        'email_file,expected_event_details',
        (
            (
                'email_samples/valid/outlook_online/sample.eml',
                {
                    'subject': 'test meet',
                    'start': datetime(2019, 3, 29, 12, 00, tzinfo=utc),
                    'end': datetime(2019, 3, 29, 12, 30, tzinfo=utc),
                    'sent': datetime(2019, 3, 29, 11, 28, 24, tzinfo=utc),
                    'location': (
                        'SOMEWHERE Agency (10 Tunstall Studios, 34-44 Tunstall Road, '
                        '10/11 Tunstall Studios, London, England, United Kingdom)'
                    ),
                    'status': 'CONFIRMED',
                    'uid': (
                        '040000008200E00074C5B7101A82E008000000001670528522E6D40100000'
                        '000000000001000000079ABFE8513989A49988F0CF2BF5B0F5A'
                    ),
                },
            ),
            (
                'email_samples/valid/gmail/sample.eml',
                {
                    'subject': 'initial',
                    'start': datetime(2019, 3, 29, 16, 30, tzinfo=utc),
                    'end': datetime(2019, 3, 29, 17, 30, tzinfo=utc),
                    'sent': datetime(2019, 3, 29, 11, 36, 33, tzinfo=utc),
                    'location': '',
                    'status': 'CONFIRMED',
                    'uid': '5iggr1e2luglss6c789b0scvgr@google.com',
                },
            ),
            (
                'email_samples/valid/gmail/no_vcalendar.eml',
                {
                    'subject': 'initial',
                    'start': datetime(2019, 3, 29, 16, 30, tzinfo=utc),
                    'end': datetime(2019, 3, 29, 17, 30, tzinfo=utc),
                    'sent': datetime(2019, 3, 29, 11, 36, 33, tzinfo=utc),
                    'location': (
                        'Somewhere, Unit FF - 305 - شارع المركز المالي - دبي - '
                        'United Arab Emirates'
                    ),
                    'status': 'CONFIRMED',
                    'uid': '5iggr1e2luglss6c789b0scvgr@google.com',
                },
            ),
            # Sample email only specifies the day for start/end instead of date/time
            (
                'email_samples/valid/outlook_iphone/sample.eml',
                {
                    'subject': 'Test meeting iPhone 5',
                    'start': datetime(2019, 5, 19, tzinfo=utc),
                    'end': datetime(2019, 5, 20, tzinfo=utc),
                    'sent': datetime(2019, 5, 13, 10, 34, 50, tzinfo=utc),
                    'location': '',
                    'status': 'CONFIRMED',
                    'uid': (
                        '040000008200E00074C5B7101A82E00800000000CCE64C7E7709D50100000000000000001'
                        '00000008EC4E55E2F36B445B797B8311D1418AE'
                    ),
                },
            ),
            (
                'email_samples/valid/outlook_desktop/sample.eml',
                {
                    'subject': 'Meeting test outlook desktop',
                    'start': datetime(2019, 5, 15, 11, 00, 00, tzinfo=utc),
                    'end': datetime(2019, 5, 15, 11, 30, 00, tzinfo=utc),
                    'sent': datetime(2019, 5, 13, 10, 52, 32, tzinfo=utc),
                    'location': 'Windsor House',
                    'status': 'CONFIRMED',
                    'uid': (
                        '040000008200E00074C5B7101A82E00800000000399124F77909D501000000'
                        '000000000010000000DC13FAF364693E4F8EEFE8C770F1C748'
                    ),
                },
            ),
        ),
    )
    def test_extract_and_vailidate_calendar_event_metadata(
        self,
        email_file,
        expected_event_details,
    ):
        """
        Verify that the get_calendar_event_metadata method extracts the expected
        data from a given email message.
        """
        parser = self._get_parser_for_email_file(email_file)
        calendar_event = parser._extract_and_validate_calendar_event_metadata()
        assert calendar_event == expected_event_details

    @pytest.mark.parametrize(
        'email_file,expected_interaction_data',
        (
            # Test that interaction data can be extracted for a simple case
            (
                'email_samples/valid/outlook_online/sample.eml',
                {
                    'adviser_email': 'adviser1@trade.gov.uk',
                    'contact_details': [
                        ('bill.adama@example.net', 'Company 1'),
                    ],
                    'secondary_adviser_emails': [],
                    'top_company_name': 'Company 1',
                    'date': datetime(2019, 3, 29, 12, 0, tzinfo=utc),
                    'location': (
                        'SOMEWHERE Agency (10 Tunstall Studios, 34-44 '
                        'Tunstall Road, 10/11 Tunstall Studios, London, '
                        'England, United Kingdom)'
                    ),
                    'subject': 'test meet',
                },
            ),
            # Test that interaction data can be extracted for a complicated case
            # with many advisers, contacts and some unknown contacts,
            # sample uses sender adviser's contact_email which is different to their email,
            # email's From field has different case to the saved Adviser's contact_email field
            (
                'email_samples/valid/gmail/sample.eml',
                {
                    'adviser_email': 'adviser3@digital.trade.gov.uk',
                    'contact_details': [
                        ('bill.adama@example.net', 'Company 1'),
                        ('saul.tigh@example.net', 'Company 1'),
                        ('laura.roslin@example.net', 'Company 2'),
                        ('sharon.valerii@example.net', 'Company 1'),
                    ],
                    'secondary_adviser_emails': ['adviser2@digital.trade.gov.uk'],
                    'top_company_name': 'Company 1',
                    'date': datetime(2019, 3, 29, 16, 30, tzinfo=utc),
                    'location': '',
                    'subject': 'initial',
                },
            ),
        ),
    )
    def test_extract_interaction_data_from_email(
        self,
        email_file,
        expected_interaction_data,
        calendar_data_fixture,
    ):
        """
        Functional test to ensure that interaction data is extracted as expected
        from an email.
        """
        parser = self._get_parser_for_email_file(email_file)
        interaction_data = parser.extract_interaction_data_from_email()
        assert interaction_data['sender'].email == expected_interaction_data['adviser_email']
        contacts = interaction_data['contacts']
        expected_contacts = expected_interaction_data['contact_details'][:]
        for contact in contacts:
            expected_contacts.remove((contact.email, contact.company.name))
        assert len(expected_contacts) == 0
        secondary_adviser_emails = {
            adviser.email for adviser in interaction_data['secondary_advisers']
        }
        expected_secondary_adviser_emails = expected_interaction_data['secondary_adviser_emails']
        assert secondary_adviser_emails == set(expected_secondary_adviser_emails)
        assert (
            interaction_data['top_company'].name == expected_interaction_data['top_company_name']
        )
        assert interaction_data['date'] == expected_interaction_data['date']
        assert interaction_data['location'] == expected_interaction_data['location']
        assert interaction_data['subject'] == expected_interaction_data['subject']

    @pytest.mark.parametrize(
        'email_file,expected_error',
        (
            (
                'email_samples/invalid/email_not_sent_by_dit.eml',
                ValidationError(
                    'The meeting email did not pass our minimal checks '
                    'to be verified as having been sent by a valid DIT '
                    'Adviser email domain.',
                ),
            ),
            (
                'email_samples/invalid/no_from_header.eml',
                ValidationError('Email was malformed - missing "from" header'),
            ),
            (
                'email_samples/invalid/email_not_sent_by_known_adviser.eml',
                ValidationError('Email not sent by recognised DIT Adviser'),
            ),
            (
                'email_samples/invalid/email_contacts_unknown.eml',
                ValidationError(
                    'No email recipients were recognised as company '
                    'contacts in Data Hub - please ensure that at least '
                    'one recipient is a company contact known by Data Hub.',
                ),
            ),
            # Calendar entry does not start with "BEGIN:VCALENDAR"
            (
                'email_samples/invalid/bad_calendar_event.eml',
                ValidationError(
                    'No calendar event could be extracted - '
                    'the iCalendar attachment was either missing or badly formatted.',
                ),
            ),
            # Calendar entry does not include an "END:VEVENT"
            (
                'email_samples/invalid/bad_calendar_event_2.eml',
                ValidationError(
                    'No calendar event could be extracted - '
                    'the iCalendar attachment was either missing or badly formatted.',
                ),
            ),
            (
                'email_samples/invalid/no_calendar_in_email.eml',
                ValidationError(
                    'No calendar event could be extracted - '
                    'the iCalendar attachment was either missing or badly formatted.',
                ),
            ),
            (
                'email_samples/invalid/no_calendar_event.eml',
                ValidationError('No calendar event was found in the iCalendar attachment.'),
            ),
            (
                'email_samples/invalid/multiple_calendar_events.eml',
                ValidationError(
                    'There were 3 events in the calendar - expected 1 event '
                    'in the iCalendar attachment.',
                ),
            ),
            (
                'email_samples/invalid/calendar_event_unconfirmed.eml',
                ValidationError('The calendar event was not status: CONFIRMED.'),
            ),
        ),
    )
    def test_extract_interaction_data_from_email_raises_error(
        self,
        email_file,
        expected_error,
        calendar_data_fixture,
    ):
        """
        Functional test to ensure that the extract_interaction_data_from_email method
        raises ValidationErrors as expected in a number of situations.
        """
        parser = self._get_parser_for_email_file(email_file)
        with pytest.raises(expected_error.__class__) as excinfo:
            parser.extract_interaction_data_from_email()
        assert excinfo.value.args[0] == expected_error.args[0]
