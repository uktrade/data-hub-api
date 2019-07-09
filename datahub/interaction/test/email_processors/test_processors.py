from datetime import datetime
from unittest import mock
from uuid import UUID

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.timezone import utc

from datahub.company.models import Advisor, Company, Contact
from datahub.interaction.email_processors.processors import CalendarInteractionEmailProcessor
from datahub.interaction.models import Interaction

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@pytest.fixture()
def base_interaction_data_fixture():
    """
    Basic interaction data spec which can be used to build a return value
    which a mock of CalendarInteractionEmailParser can return.
    """
    return {
        'sender_email': 'adviser1@trade.gov.uk',
        'contact_emails': ['bill.adama@example.net', 'saul.tigh@example.net'],
        'secondary_adviser_emails': [],
        'date': datetime(2019, 5, 1, 13, 00, tzinfo=utc),
        'top_company_name': 'Company 1',
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
        """
        Given a spec of interaction data and monkeypatch object, sets a mocked
        return value for CalendarInteractionEmailParser.extract_interaction_data_from_email.
        """
        email_parser_mock = mock.Mock()
        monkeypatch.setattr(
            (
                'datahub.interaction.email_processors.parsers.CalendarInteractionEmailParser'
                '.extract_interaction_data_from_email'
            ),
            email_parser_mock,
        )
        contacts = list(Contact.objects.filter(email__in=interaction_data['contact_emails']))
        secondary_advisers = list(
            Advisor.objects.filter(email__in=interaction_data['secondary_adviser_emails']),
        )
        email_parser_mock.return_value = {
            'sender': Advisor.objects.get(email=interaction_data['sender_email']),
            'contacts': contacts,
            'secondary_advisers': secondary_advisers,
            'top_company': Company.objects.get(name=interaction_data['top_company_name']),
            'date': interaction_data['date'],
            'location': interaction_data['location'],
            'meeting_details': interaction_data['meeting_details'],
            'subject': interaction_data['subject'],
        }
        return email_parser_mock

    @pytest.mark.parametrize(
        'interaction_data_overrides,expected_subject',
        (
            # Simple case; just the base interaction data
            (
                {},
                'Meeting between Adviser 1, Bill Adama and Saul Tigh',
            ),
            # Including secondary advisers
            (
                {
                    'secondary_adviser_emails': [
                        'adviser2@digital.trade.gov.uk',
                        'adviser3@digital.trade.gov.uk',
                    ],
                },
                'Meeting between Adviser 1, Adviser 2, Adviser 3, Bill Adama and Saul Tigh',
            ),
            # Contacts from different companies
            (
                {
                    'contact_emails': [
                        'bill.adama@example.net',
                        'laura.roslin@example.net',
                    ],
                },
                'Meeting between Adviser 1 and Bill Adama',
            ),
        ),
    )
    def test_process_email_successful(
        self,
        interaction_data_overrides,
        expected_subject,
        calendar_data_fixture,
        base_interaction_data_fixture,
        monkeypatch,
    ):
        """
        Test that process_email saves a draft interaction when the calendar
        parser yields good data.
        """
        interaction_data = {
            **base_interaction_data_fixture,
            **interaction_data_overrides,
        }
        email_parser_mock = self._get_email_parser_mock(interaction_data, monkeypatch)

        # Process the message and save a draft interaction
        processor = CalendarInteractionEmailProcessor()
        result, message = processor.process_email(mock.Mock())
        assert result is True
        interaction = Interaction.objects.get(source__meeting__id='12345')
        assert message == f'Successfully created interaction #{interaction.id}'

        # Verify dit_participants holds all of the advisers for the interaction
        expected_adviser_emails = {
            interaction_data['sender_email'],
            *interaction_data['secondary_adviser_emails'],
        }
        interaction_adviser_emails = {
            participant.adviser.email for participant
            in interaction.dit_participants.all()
        }
        assert interaction_adviser_emails == expected_adviser_emails

        # Verify contacts holds all of the expected contacts for the interaction
        interaction_contacts = interaction.contacts.all()
        email_contacts = email_parser_mock.return_value['contacts']
        for contact in email_contacts:
            if contact.company.name == interaction_data['top_company_name']:
                assert contact in interaction_contacts
        assert interaction.company.name == interaction_data['top_company_name']
        assert interaction.date == interaction_data['date']
        assert interaction.location == interaction_data['location']
        assert interaction.source == {
            'meeting': {'id': interaction_data['meeting_details']['uid']},
        }
        assert interaction.subject == expected_subject
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
            dit_participants__adviser=Advisor.objects.get(email=interaction_data['sender_email']),
        )
        assert all_interactions_by_sender.count() == 1
        assert all_interactions_by_sender[0].id == UUID(interaction_id)

    def test_process_email_parser_validation_error(
        self,
        base_interaction_data_fixture,
        calendar_data_fixture,
        monkeypatch,
    ):
        """
        Test that process_email returns an expected message when the parser
        raises a ValidationError.
        """
        interaction_data = {**base_interaction_data_fixture}
        mock_parser = self._get_email_parser_mock(interaction_data, monkeypatch)
        error_message = 'There was a problem with the meeting format'
        mock_parser.side_effect = ValidationError(error_message)
        processor = CalendarInteractionEmailProcessor()
        # Create the calendar interaction initially
        result, message = processor.process_email(mock.Mock())
        assert result is False
        assert message == error_message

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
            # No contacts present
            (
                {
                    'contact_emails': [],
                },
                'contacts: This list may not be empty.',
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
