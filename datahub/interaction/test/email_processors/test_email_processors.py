import os
from datetime import date, datetime

import mailparser
import pytest
import pytz
from django.core.exceptions import ValidationError

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.interaction.email_processors import CalendarInteractionEmailParser


@pytest.fixture()
def calendar_data_fixture():
    """
    Create advisers, contacts and companies so that our email samples can be
    attributed to some DB entities.
    """
    fixture = {
        'contacts': [],
        'advisers': [],
    }
    adviser_emails = [
        'brendan.smith@trade.gov.uk',
        'marco.fucci@digital.trade.gov.uk',
        'ali.zaidi@digital.trade.gov.uk',
    ]
    for adviser_email in adviser_emails:
        fixture['advisers'].append(
            AdviserFactory(contact_email=adviser_email, email=adviser_email),
        )
    fixture['company_1'] = CompanyFactory(name='Company 1')
    fixture['company_2'] = CompanyFactory(name='Company 2')
    contacts = [
        ('Bill Adama', fixture['company_1']),
        ('Saul Tigh', fixture['company_1']),
        ('Laura Roslin', fixture['company_2']),
    ]
    for name, company in contacts:
        first_name, last_name = name.split(' ')
        email_prefix = name.lower().replace(' ', '.')
        email = f'{email_prefix}@example.net'
        fixture['contacts'].append(ContactFactory(
            first_name=first_name,
            last_name=last_name,
            email=email,
            company=company,
        ))
    yield fixture


@pytest.mark.django_db
class TestCalendarInteractionEmailParser:
    """
    Test the CalendarInteractionEmailProcessor class.
    """

    def _get_parser_for_email_file(self, relative_email_file_path):
        email_file_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            relative_email_file_path,
        )
        message = mailparser.parse_from_file(email_file_path)
        return CalendarInteractionEmailParser(message)

    @pytest.mark.parametrize(
        'email_file,expected_event_details',
        (
            (
                'email_samples/valid/outlook_online/sample.eml',
                {
                    'subject': 'Meeting test outlook online',
                    'start': datetime(2019, 5, 15, 11, 30, tzinfo=pytz.utc),
                    'end': datetime(2019, 5, 15, 12, 30, tzinfo=pytz.utc),
                    'sent': datetime(2019, 5, 13, 12, 32, 53, tzinfo=pytz.utc),
                    'location': (
                        'Someplace Else - The Park (The Park Hotel, Ground Floor, Near '
                        'Delhi Public School, Park Street, Kolkata West Bengal, India)'
                    ),
                    'status': 'CONFIRMED',
                    'uid': (
                        '040000008200E00074C5B7101A82E008000000002D3F6AFC8709D50100000'
                        '00000000000100000009769D9995082A348A13B8F12B2FAB9B0'
                    ),
                },
            ),
            (
                'email_samples/valid/gmail/sample.eml',
                {
                    'subject': 'Test meeting gmail',
                    'start': datetime(2019, 5, 13, 14, 00, tzinfo=pytz.utc),
                    'end': datetime(2019, 5, 13, 15, 00, tzinfo=pytz.utc),
                    'sent': datetime(2019, 5, 13, 12, 37, 25, tzinfo=pytz.utc),
                    'location': '',
                    'status': 'CONFIRMED',
                    'uid': '0rmcu1vgucemr7jtbenaknlq11@google.com',
                },
            ),
            (
                'email_samples/valid/gmail/no_vcalendar.eml',
                {
                    'subject': 'initial',
                    'start': datetime(2019, 3, 29, 16, 30, tzinfo=pytz.utc),
                    'end': datetime(2019, 3, 29, 17, 30, tzinfo=pytz.utc),
                    'sent': datetime(2019, 3, 29, 11, 36, 33, tzinfo=pytz.utc),
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
                    'sent': datetime(2019, 5, 13, 10, 34, 50, tzinfo=pytz.utc),
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
                    'start': datetime(2019, 5, 15, 11, 00, 00, tzinfo=pytz.utc),
                    'end': datetime(2019, 5, 15, 11, 30, 00, tzinfo=pytz.utc),
                    'sent': datetime(2019, 5, 13, 10, 52, 32, tzinfo=pytz.utc),
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
    def test_get_calendar_event_metadata(self, email_file, expected_event_details):
        """
        Verify that the get_calendar_event_metadata method extracts the expected
        data from a given email message.
        """
        parser = self._get_parser_for_email_file(email_file)
        calendar_event = parser._get_calendar_event_metadata()
        assert(calendar_event == expected_event_details)

    @pytest.mark.parametrize(
        'email_file,expected_interaction_data',
        (
            # Test that interaction data can be extracted for an easy case
            (
                'email_samples/valid/outlook_online/initial.eml',
                {
                    'adviser_email': 'brendan.smith@trade.gov.uk',
                    'contact_emails': ['bill.adama@example.net'],
                    'secondary_adviser_emails': [],
                    'company_name': 'Company 1',
                    'date': datetime(2019, 3, 29, 12, 0, tzinfo=pytz.utc),
                    'location': (
                        'SOMEWHERE Agency (10 Tunstall Studios, 34-44 '
                        'Tunstall Road, 10/11 Tunstall Studios, London, '
                        'England, United Kingdom)'
                    ),
                    'subject': 'test meet',
                },
            ),
            # Test that interaction data can be extracted for a complicated case
            # with many advisers, contacts and some unknown contacts
            (
                'email_samples/valid/gmail/initial.eml',
                {
                    'adviser_email': 'brendan.smith@trade.gov.uk',
                    'contact_emails': [
                        'bill.adama@example.net',
                        'saul.tigh@example.net',
                        'laura.roslin@example.net',
                    ],
                    'secondary_adviser_emails': ['marco.fucci@digital.trade.gov.uk'],
                    'company_name': 'Company 1',
                    'date': datetime(2019, 3, 29, 16, 30, tzinfo=pytz.utc),
                    'location': (
                        'Somewhere, Unit FF - 305 - شارع المركز المالي - دبي - '
                        'United Arab Emirates'
                    ),
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
        for contact in interaction_data['contacts']:
            assert contact.email in expected_interaction_data['contact_emails']
        for adviser in interaction_data['secondary_advisers']:
            assert adviser.email in expected_interaction_data['secondary_adviser_emails']
        assert interaction_data['date'] == expected_interaction_data['date']
        assert interaction_data['location'] == expected_interaction_data['location']
        assert interaction_data['subject'] == expected_interaction_data['subject']

    @pytest.mark.parametrize(
        'email_file,expected_error',
        (
            (
                'email_samples/invalid/email_not_sent_by_dit.eml',
                ValidationError('Email not sent by DIT'),
            ),
            (
                'email_samples/invalid/email_not_sent_by_known_adviser.eml',
                ValidationError('Email not sent by recognised DIT Adviser'),
            ),
            (
                'email_samples/invalid/email_contacts_unknown.eml',
                ValidationError('No email recipients were recognised as Contacts'),
            ),
            (
                'email_samples/invalid/bad_calendar_event.eml',
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
        with pytest.raises(expected_error.__class__) as exc:
            parser.extract_interaction_data_from_email()
        assert exc.value.message == expected_error.message
