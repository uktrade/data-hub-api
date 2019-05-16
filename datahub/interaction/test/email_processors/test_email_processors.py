from datetime import date, datetime
from pathlib import PurePath
from unittest import mock
from uuid import UUID

import factory
import mailparser
import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.timezone import utc

from datahub.company.models.adviser import Advisor
from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.interaction.email_processors import (
    CalendarInteractionEmailParser,
    CalendarInteractionEmailProcessor,
)
from datahub.interaction.models import Interaction

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


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
        'adviser1@trade.gov.uk',
        'adviser2@digital.trade.gov.uk',
    ]
    fixture['advisers'] = AdviserFactory.create_batch(
        len(adviser_emails),
        email=factory.Iterator(adviser_emails),
        contact_email=factory.SelfAttribute('email'),
    )
    adviser_different_correspondence = AdviserFactory(
        email='adviser3@digital.trade.gov.uk',
        contact_email='correspondence3@digital.trade.gov.uk',
    )
    fixture['advisers'].append(adviser_different_correspondence)
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
        contact = ContactFactory(
            first_name=first_name,
            last_name=last_name,
            email=email,
            company=company,
        )
        fixture['contacts'].append(contact)
    yield fixture


@pytest.fixture()
def base_interaction_data_fixture():
    """
    Basic interaction data which a mock of CalendarInteractionEmailParser can return.
    """
    return {
        'sender': 'brendan.smith@trade.gov.uk',
        'contacts': ['bill.adama@example.net', 'saul.tigh@example.net'],
        'secondary_advisers': [],
        'date': datetime(2019, 5, 1, 13, 00, tzinfo=utc),
        'company': 'Company 1',
        'location': 'Windsor House',
        'meeting_details': {'uid': '12345'},
        'subject': 'A meeting',
    }


@pytest.mark.django_db
class TestCalendarInteractionEmailProcessor:
    """
    Test the CalendarInteractionEmailProcessor class.
    """

    def _get_email_parser_mock(self, interaction_data, monkeypatch):
        email_parser_mock = mock.Mock()
        monkeypatch.setattr(
            (
                'datahub.interaction.email_processors.CalendarInteractionEmailParser'
                '.extract_interaction_data_from_email'
            ),
            email_parser_mock,
        )
        contacts = list(Contact.objects.filter(email__in=interaction_data['contacts']))
        secondary_advisers = list(
            Advisor.objects.filter(email__in=interaction_data['secondary_advisers']),
        )
        email_parser_mock.return_value = {
            'sender': Advisor.objects.get(email=interaction_data['sender']),
            'contacts': contacts,
            'secondary_advisers': secondary_advisers,
            'company': Company.objects.get(name=interaction_data['company']),
            'date': interaction_data['date'],
            'location': interaction_data['location'],
            'meeting_details': interaction_data['meeting_details'],
            'subject': interaction_data['subject'],
        }
        return email_parser_mock

    @pytest.mark.parametrize(
        'interaction_data_overrides',
        (
            # Simple case; just the base interaction data
            {},
            # Including secondary advisers
            {
                'secondary_advisers': [
                    'marco.fucci@digital.trade.gov.uk',
                    'ali.zaidi@digital.trade.gov.uk',
                ],
            },
        ),
    )
    def test_process_email_successful(
        self,
        interaction_data_overrides,
        calendar_data_fixture,
        base_interaction_data_fixture,
        monkeypatch,
    ):
        """
        Test that process_email saves a draft interaction can be saved successfully
        when the calendar parser yields good data.
        """
        interaction_data = {**base_interaction_data_fixture, **interaction_data_overrides}
        self._get_email_parser_mock(interaction_data, monkeypatch)
        processor = CalendarInteractionEmailProcessor()
        result, message = processor.process_email(mock.Mock())
        assert result is True
        interaction_id = message.split()[-1].strip('#')
        interaction = Interaction.objects.get(id=interaction_id)
        # Verify dit_participants holds all of the advisers for the interaction
        expected_advisers = [interaction_data['sender']]
        expected_advisers.extend(interaction_data['secondary_advisers'])
        interaction_advisers = interaction.dit_participants.all()
        for participant in interaction_advisers:
            assert participant.adviser.email in expected_advisers
        assert interaction_advisers.count() == len(expected_advisers)
        # Verify contacts holds all of the contacts for the interaction
        interaction_contacts = interaction.contacts.all()
        for contact in interaction_contacts:
            assert contact.email in interaction_data['contacts']
        assert len(interaction_data['contacts']) == interaction_contacts.count()
        assert interaction.company.name == interaction_data['company']
        assert interaction.date == interaction_data['date']
        assert interaction.location == interaction_data['location']
        assert interaction.source == {
            'type': Interaction.SOURCE_TYPES.meeting,
            'id': interaction_data['meeting_details']['uid'],
        }
        assert interaction.subject == interaction_data['subject']
        assert interaction.status == Interaction.STATUSES.draft

    def test_process_email_meeting_exists(
        self,
        base_interaction_data_fixture,
        calendar_data_fixture,
        monkeypatch,
    ):
        """
        Test that process_email does not save another interaction when the meeting
        already exists as an interaction.
        """
        interaction_data = {**base_interaction_data_fixture}
        self._get_email_parser_mock(interaction_data, monkeypatch)
        processor = CalendarInteractionEmailProcessor()
        # Create the calendar interaction initially
        initial_result, initial_message = processor.process_email(mock.Mock())
        interaction_id = initial_message.split()[-1].strip('#')
        assert initial_result is True
        # Simulate processing the email again
        duplicate_result, duplicate_message = processor.process_email(mock.Mock())
        assert duplicate_result is False
        assert duplicate_message == 'Meeting already exists as an interaction'
        all_interactions_by_sender = Interaction.objects.filter(
            dit_participants__adviser=Advisor.objects.get(email=interaction_data['sender']),
        )
        assert all_interactions_by_sender.count() == 1
        assert all_interactions_by_sender[0].id == UUID(interaction_id)

    @pytest.mark.parametrize(
        'interaction_data_overrides,expected_message',
        (
            # string fields too long
            (
                {
                    'location': 'x' * (MAX_LENGTH + 1),
                },
                'location: Ensure this field has no more than 255 characters.',
            ),
        ),
    )
    def test_process_email_validation(
        self,
        interaction_data_overrides,
        expected_message,
        base_interaction_data_fixture,
        calendar_data_fixture,
        monkeypatch,
    ):
        """
        Test that process_email returns expected validation error messages when
        called with invalid data.
        """
        interaction_data = {**base_interaction_data_fixture, **interaction_data_overrides}
        self._get_email_parser_mock(interaction_data, monkeypatch)
        processor = CalendarInteractionEmailProcessor()
        # Create the calendar interaction initially
        result, message = processor.process_email(mock.Mock())
        assert result is False
        assert message == expected_message


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
                    'company_name': 'Company 1',
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
                    'company_name': 'Company 1',
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
        for contact in interaction_data['contacts']:
            assert contact.email in expected_interaction_data['contact_emails']
        for adviser in interaction_data['secondary_advisers']:
            assert adviser.email in expected_interaction_data['secondary_adviser_emails']
        assert interaction_data['top_company'].name == expected_interaction_data['company_name']
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
        with pytest.raises(expected_error.__class__) as exc:
            parser.extract_interaction_data_from_email()
        assert exc.value.message == expected_error.message
