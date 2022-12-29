import logging
from datetime import datetime
from unittest import mock
from uuid import UUID

import pytest
from django.conf import settings
from django.utils.timezone import utc

from datahub.company.models import Advisor, Company, Contact
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction import INTERACTION_EMAIL_NOTIFICATION_FEATURE_FLAG_NAME
from datahub.interaction.email_processors.exceptions import (
    BadCalendarInviteError,
    MalformedEmailError,
    NoContactsError,
    SenderUnverifiedError,
    UnconfirmedCalendarInviteError,
)
from datahub.interaction.email_processors.notify import Template
from datahub.interaction.email_processors.processors import (
    CalendarInteractionEmailProcessor,
    EXCEPTION_NOTIFY_MESSAGES,
)
from datahub.interaction.models import Interaction


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@pytest.fixture()
def interaction_email_notification_feature_flag():
    """
    Creates the email ingestion feature flag.
    """
    yield FeatureFlagFactory(code=INTERACTION_EMAIL_NOTIFICATION_FEATURE_FLAG_NAME)


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
        'meeting_details': {'uid': '12345'},
        'subject': 'A meeting',
    }


@pytest.fixture
def mock_notify_adviser_by_email(monkeypatch):
    """
    Mocks the notify_adviser_by_email function.
    """
    mock_notify_adviser_by_email = mock.Mock()
    monkeypatch.setattr(
        'datahub.interaction.email_processors.notify.notify_adviser_by_email',
        mock_notify_adviser_by_email,
    )
    return mock_notify_adviser_by_email


@pytest.fixture
def mock_message(base_interaction_data_fixture):
    """
    Mock email messsage.
    """
    message = mock.Mock()
    message.from_ = [(None, base_interaction_data_fixture['sender_email'])]
    message.to = [
        (None, email)
        for email in base_interaction_data_fixture['contact_emails']
    ]
    message.cc = []
    message.message_id = 'abc123'
    message.received = [{'date_utc': '2019-08-01T00:00:01'}]
    return message


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
        mock_notify_adviser_by_email,
        interaction_email_notification_feature_flag,
        mock_message,
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
        result, message = processor.process_email(mock_message)
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
        assert interaction.source == {
            'meeting': {'id': interaction_data['meeting_details']['uid']},
        }
        assert interaction.subject == expected_subject
        assert interaction.status == Interaction.Status.DRAFT

        sender_participant = interaction.dit_participants.get(
            adviser__email__iexact=interaction_data['sender_email'],
        )
        mock_notify_adviser_by_email.assert_called_once_with(
            sender_participant.adviser,
            Template.meeting_ingest_success.value,
            context={
                'interaction_url': interaction.get_absolute_url(),
                'recipients': 'bill.adama@example.net, saul.tigh@example.net',
                'support_team_email': settings.DATAHUB_SUPPORT_EMAIL_ADDRESS,
            },
        )

    def test_process_email_meeting_exists(
        self,
        base_interaction_data_fixture,
        calendar_data_fixture,
        interaction_email_notification_feature_flag,
        mock_message,
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
        initial_result, initial_message = processor.process_email(mock_message)
        interaction_id = initial_message.split()[-1].strip('#')
        assert initial_result is True
        # Simulate processing the email again
        duplicate_result, duplicate_message = processor.process_email(mock_message)
        assert duplicate_result is False
        assert duplicate_message == 'Meeting already exists as an interaction'
        all_interactions_by_sender = Interaction.objects.filter(
            dit_participants__adviser=Advisor.objects.get(email=interaction_data['sender_email']),
        )
        assert all_interactions_by_sender.count() == 1
        assert all_interactions_by_sender[0].id == UUID(interaction_id)

    @pytest.mark.parametrize(
        'invalid_invite_exception_class,expected_to_notify',
        (
            (
                BadCalendarInviteError,
                True,
            ),
            (
                NoContactsError,
                True,
            ),
            (
                SenderUnverifiedError,
                False,
            ),
            (
                MalformedEmailError,
                False,
            ),
            (
                UnconfirmedCalendarInviteError,
                False,
            ),
        ),
    )
    def test_process_email_parser_validation_error(
        self,
        base_interaction_data_fixture,
        calendar_data_fixture,
        mock_notify_adviser_by_email,
        interaction_email_notification_feature_flag,
        mock_message,
        monkeypatch,
        caplog,
        invalid_invite_exception_class,
        expected_to_notify,
    ):
        """
        Test that process_email returns an expected message when the parser
        raises a ValidationError.
        """
        caplog.set_level(logging.WARNING)
        interaction_data = {**base_interaction_data_fixture}
        mock_parser = self._get_email_parser_mock(interaction_data, monkeypatch)
        exception = invalid_invite_exception_class('There was a problem with the meeting format')
        mock_parser.side_effect = exception
        expected_exception_string = repr(exception)
        processor = CalendarInteractionEmailProcessor()
        result, message = processor.process_email(mock_message)
        assert result is False
        assert message == expected_exception_string
        expected_log = (
            'datahub.interaction.email_processors.processors',
            30,
            'Ingested email with ID "abc123" (received 2019-08-01T00:00:01) '
            f'was not valid: {expected_exception_string}',
        )
        assert expected_log in caplog.record_tuples
        if expected_to_notify:
            expected_error_message = (
                EXCEPTION_NOTIFY_MESSAGES[invalid_invite_exception_class]
            )
            mock_notify_adviser_by_email.assert_called_once_with(
                Advisor.objects.filter(
                    email=base_interaction_data_fixture['sender_email'],
                ).first(),
                Template.meeting_ingest_failure.value,
                context={
                    'errors': [expected_error_message],
                    'recipients': ', '.join(base_interaction_data_fixture['contact_emails']),
                    'support_team_email': settings.DATAHUB_SUPPORT_EMAIL_ADDRESS,
                },
            )
        else:
            mock_notify_adviser_by_email.assert_not_called()

    @pytest.mark.parametrize(
        'interaction_data_overrides,expected_message',
        (
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
        mock_notify_adviser_by_email,
        interaction_email_notification_feature_flag,
        mock_message,
        monkeypatch,
    ):
        """
        Test that process_email returns expected validation error messages when
        called with invalid data.
        """
        interaction_data = {**base_interaction_data_fixture, **interaction_data_overrides}
        self._get_email_parser_mock(interaction_data, monkeypatch)
        processor = CalendarInteractionEmailProcessor()
        result, message = processor.process_email(mock_message)
        assert result is False
        assert message == expected_message
        mock_notify_adviser_by_email.assert_called_once_with(
            Advisor.objects.filter(email=base_interaction_data_fixture['sender_email']).first(),
            Template.meeting_ingest_failure.value,
            context={
                'errors': [expected_message],
                'recipients': ', '.join(base_interaction_data_fixture['contact_emails']),
                'support_team_email': settings.DATAHUB_SUPPORT_EMAIL_ADDRESS,
            },
        )
