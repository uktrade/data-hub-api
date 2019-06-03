from datetime import date, datetime
from pathlib import PurePath

import mailparser
import pytest
from django.core.exceptions import ValidationError
from django.utils.timezone import utc

from datahub.interaction.email_processors.parsers import (
    CalendarInteractionEmailParser,
    EmailNotSentByDITException,
)


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
            (
                'email_samples/valid/outlook_iphone/sample.eml',
                {
                    'subject': 'Test meeting iPhone 5',
                    'start': date(2019, 5, 19),
                    'end': date(2019, 5, 20),
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
                    'contact_emails': ['bill.adama@example.net'],
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
            # sample uses sender adviser's contact_email which is different to their email
            (
                'email_samples/valid/gmail/sample.eml',
                {
                    'adviser_email': 'adviser3@digital.trade.gov.uk',
                    'contact_emails': [
                        'bill.adama@example.net',
                        'saul.tigh@example.net',
                        'laura.roslin@example.net',
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
        contact_emails = {contact.email for contact in interaction_data['contacts']}
        assert contact_emails == set(expected_interaction_data['contact_emails'])
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
                # TODO: Swap this expected error out for a ValidationError when
                # we are past the pilot stage for email ingestion
                EmailNotSentByDITException(
                    'Email with ID "<CWXP123MB2008236F14A5E2A22B2B65FFC90F0@CWXP123MB2008.'
                    'GBRP123.PROD.OUTLOOK.COM>" and sender domain "unknown.net" was not recognised'
                    ' as being sent by an authenticated DIT domain. Either the domain was '
                    'unrecognised, or it did not pass our requirements for Authentication-Results.'
                    ' Further investigation is needed during the pilot for email ingestion.',
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
                ValidationError('No email recipients were recognised as Contacts'),
            ),
            # Calendar entry does not start with "BEGIN:VCALENDAR"
            (
                'email_samples/invalid/bad_calendar_event.eml',
                ValidationError('No calendar event could be extracted'),
            ),
            # Calendar entry does not include an "END:VEVENT"
            (
                'email_samples/invalid/bad_calendar_event_2.eml',
                ValidationError('No calendar event could be extracted'),
            ),
            (
                'email_samples/invalid/no_calendar_in_email.eml',
                ValidationError('No calendar event could be extracted'),
            ),
            (
                'email_samples/invalid/no_calendar_event.eml',
                ValidationError('No calendar event was found in the calendar'),
            ),
            (
                'email_samples/invalid/multiple_calendar_events.eml',
                ValidationError(
                    'There were 3 events in the calendar '
                    '- expected 1 event',
                ),
            ),
            (
                'email_samples/invalid/calendar_event_unconfirmed.eml',
                ValidationError('Calendar event was not status: CONFIRMED'),
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
