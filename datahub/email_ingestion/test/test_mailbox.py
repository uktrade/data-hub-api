import copy
from email.errors import MessageParseError
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings

from datahub.email_ingestion.email_processor import EmailProcessor
from datahub.email_ingestion.mailbox import Mailbox, MailboxHandler
from datahub.email_ingestion.test.utils import (
    BAD_MAILBOXES_SETTING,
    MAILBOXES_SETTING,
    mock_import_string,
)

EXPECTED_EMAIL_MESSAGES = [
    {
        'uid': 'abc1',
        'message_content': 'abc1foobar',
    },
    {
        'uid': 'abc2',
        'message_content': 'abc2foobar',
    },
    {
        'uid': 'abc3',
        'message_content': 'abc3foobar',
    },
]


def _get_mocked_imap(email_messages, mocked_imap_class):
    mocked_imap = mocked_imap_class.return_value
    email_ids = [message['uid'] for message in email_messages]
    email_bodies = {
        message['uid']: message['message_content'].encode('utf-8')
        for message in email_messages
    }
    encoded_ids = ' '.join(email_ids).encode('utf-8')

    # Set our mocked imap server's uid method to return certain values
    # when called with certain signatures
    def uid_side_effect(action, *args):
        # A search call should return our email message ids
        if action == 'search':
            return (None, (encoded_ids,))
        # Fetch calls should return the email message bodies in the expected
        # format
        if action == 'fetch':
            # The expected format is pretty naff...
            return (None, ((None, email_bodies[args[0]]),))
    mocked_imap.uid.side_effect = uid_side_effect
    return mocked_imap


def patch_imap(email_messages):
    """
    Decorator to patch IMAP4_SSL which is used in the Mailbox
    class. We can specify email details returned by our mocked instance by
    providing sample email messages.

    :param email_messages: iterable of email message dictionaries with keys
        uid (the email uid) and message_content (a string of message payload)
    """
    def patch_imap_decorator(function):
        def wrapper(self, *args, **kwargs):
            with mock.patch('datahub.email_ingestion.mailbox.imaplib.IMAP4_SSL') as imap_class:
                mocked_imap = _get_mocked_imap(email_messages, imap_class)
                retval = function(self, mocked_imap, *args, **kwargs)
                return retval
        return wrapper
    return patch_imap_decorator


class MockedParsedMessage(str):
    """
    A simple mock to replace MailParser objects - subclassing string is convenient
    for equality checks.
    """

    message_id = 'foobar'


class TestMailbox:
    """
    Test the Mailbox class.
    """

    def mock_mailbox_parse_message(self, mailbox):
        """
        Helper to ensure that the parse_message method of a supplied mailbox
        object is mocked.
        """
        mailbox._parse_message = mock.Mock()

        def parse_message_side_effect(message_body_bytes):
            parsed_message = MockedParsedMessage(message_body_bytes.decode())
            return parsed_message
        mailbox._parse_message.side_effect = parse_message_side_effect

    @patch_imap(EXPECTED_EMAIL_MESSAGES)
    def test_get_new_mail(self, mocked_imap):
        """
        Functional test for get_new_mail method. We must mock out a couple of
        external dependencies here; namely the IMAP gateway and message parsing
        code.
        """
        expected_email_messages = copy.deepcopy(EXPECTED_EMAIL_MESSAGES)
        mailbox = Mailbox(
            'foobar@example.net',
            'foobarbaz1',
            'domain.example.net',
            mail_processor_classes=[],
            imap_port=465,
        )
        # Ensure that we also mock the Mailbox._parse_message method - this should
        # mean that the mailbox method gives us our messages in an expected format
        self.mock_mailbox_parse_message(mailbox)

        messages = list(mailbox.get_new_mail())
        assert len(messages) == len(expected_email_messages)
        # Go through all of the returned messages and ensure that the parsed
        # message content is as expected
        for count, message in enumerate(messages):
            expected_email_message = expected_email_messages[count]
            # Ensure that the messages our mailbox retrieves are those that we expect
            assert message == expected_email_message['message_content']
            # Ensure that a call was made to mark each message retrieved as Deleted
            mocked_imap.uid.assert_any_call(
                'store',
                expected_email_message['uid'],
                '+FLAGS',
                '(\\Deleted)',
            )
        # Ensure that the imap connection was cleaned up
        mocked_imap.expunge.assert_called_once()
        mocked_imap.close.assert_called_once()
        mocked_imap.logout.assert_called_once()

    @patch_imap([])
    def test_get_new_mail_no_new_messages(self, mocked_imap):
        """
        Functional test to ensure that get_new_mail operates as expected when
        there are no email messages to ingest.

        """
        mailbox = Mailbox(
            'foobar@example.net',
            'foobarbaz1',
            'domain.example.net',
            mail_processor_classes=[],
        )

        messages = list(mailbox.get_new_mail())
        assert messages == []

    @patch_imap(EXPECTED_EMAIL_MESSAGES)
    def test_get_new_mail_empty_message_contents(self, mocked_imap):
        """
        Functional test to ensure that the get_new_mail method can handle when
        message contents are empty and skip as appropriate.
        """
        expected_email_messages = copy.deepcopy(EXPECTED_EMAIL_MESSAGES)
        mailbox = Mailbox(
            'foobar@example.net',
            'foobarbaz1',
            'domain.example.net',
            mail_processor_classes=[],
        )

        # Ensure that we also mock the Mailbox._parse_message method - this should
        # mean that the mailbox method gives us our messages in an expected format
        self.mock_mailbox_parse_message(mailbox)

        original_side_effect = mocked_imap.uid.side_effect

        def uid_side_effect(action, *args):
            if action == 'fetch':
                uid = args[0]
                if uid == 'abc2':
                    return [None, None]
            return original_side_effect(action, *args)
        mocked_imap.uid.side_effect = uid_side_effect

        messages = list(mailbox.get_new_mail())
        # We expect that the messages returned will omit the empty message
        expected_email_messages.pop(1)
        assert len(messages) == len(expected_email_messages)
        # Go through all of the returned messages and ensure that the parsed
        # message content is as expected
        for count, message in enumerate(messages):
            expected_email_message = expected_email_messages[count]
            # Ensure that the messages our mailbox retrieves are those that we expect
            assert message == expected_email_message['message_content']
            # Ensure that a call was made to mark each message retrieved as Deleted
            mocked_imap.uid.assert_any_call(
                'store',
                expected_email_message['uid'],
                '+FLAGS',
                '(\\Deleted)',
            )

    @patch_imap(EXPECTED_EMAIL_MESSAGES)
    def test_get_new_mail_parsing_failure(self, mocked_imap):
        """
        Functional test to ensure that the get_new_mail method can handle a
        parsing failure as expected.
        """
        expected_email_messages = copy.deepcopy(EXPECTED_EMAIL_MESSAGES)
        mailbox = Mailbox(
            'foobar@example.net',
            'foobarbaz1',
            'domain.example.net',
            mail_processor_classes=[],
        )

        # Mock the Mailbox._parse_message method - this allows us to simulate
        # a problem when parsing a particular message
        mailbox._parse_message = mock.Mock()

        def parse_message_side_effect(message):
            message_str = message.decode()
            if message_str == 'abc2foobar':
                raise MessageParseError()
            return message_str
        mailbox._parse_message.side_effect = parse_message_side_effect

        messages = list(mailbox.get_new_mail())
        # We expect that the messages returned will omit the problematic message
        expected_email_messages.pop(1)
        assert len(messages) == len(expected_email_messages)
        # Go through all of the returned messages and ensure that the parsed
        # message content is as expected
        for count, message in enumerate(messages):
            expected_email_message = expected_email_messages[count]
            # Ensure that the messages our mailbox retrieves are those that we expect
            assert message == expected_email_message['message_content']
            # Ensure that a call was made to mark each message retrieved as Deleted
            mocked_imap.uid.assert_any_call(
                'store',
                expected_email_message['uid'],
                '+FLAGS',
                '(\\Deleted)',
            )
        # Ensure that the imap connection was cleaned up
        mocked_imap.close.assert_called_once()
        mocked_imap.logout.assert_called_once()

    @patch_imap(EXPECTED_EMAIL_MESSAGES)
    def test_get_new_mail_retrieval_error(self, mocked_imap):
        """
        Functional test to ensure that the get_new_mail method can handle a
        EmailRetrievalError as expected.
        """
        mailbox = Mailbox(
            'foobar@example.net',
            'foobarbaz1',
            'domain.example.net',
            mail_processor_classes=[],
        )

        # Ensure that we also mock the Mailbox._parse_message method - this should
        # mean that the mailbox method gives us our messages in an expected format
        self.mock_mailbox_parse_message(mailbox)

        original_side_effect = mocked_imap.uid.side_effect

        def uid_side_effect(action, *args):
            if action == 'fetch':
                raise TypeError
            else:
                return original_side_effect(action, *args)
        mocked_imap.uid.side_effect = uid_side_effect

        # Cast generator method call to list to force execution
        new_mail = list(mailbox.get_new_mail())
        assert new_mail == []

    @patch_imap(EXPECTED_EMAIL_MESSAGES)
    def test_process_new_mail(self, mocked_imap):
        """
        Functional test to ensure that a processor class has the opportunity to
        process messages as expected.
        """
        expected_email_messages = copy.deepcopy(EXPECTED_EMAIL_MESSAGES)
        processor_class = mock.Mock(spec=EmailProcessor)
        processor_class.__name__ = ''
        processor = processor_class.return_value
        processor.process_email.return_value = (False, 'Bad email')
        mailbox = Mailbox(
            'foobar@example.net',
            'foobarbaz1',
            'domain.example.net',
            mail_processor_classes=[processor_class],
        )
        # Ensure that we also mock the Mailbox._parse_message method - this should
        # mean that the mailbox method gives us our messages in an expected format
        self.mock_mailbox_parse_message(mailbox)

        mailbox.process_new_mail()
        for message in expected_email_messages:
            processor.process_email.assert_any_call(message['message_content'])

    @pytest.mark.parametrize(
        'processor_count,processor_results,email_processed',
        (
            # Ensure that if no processors could process the message the method
            # reports that it was not processed
            (
                3,
                (
                    (False, 'Could not be processed'),
                    (False, 'Could not be processed'),
                    (False, 'Could not be processed'),
                ),
                False,
            ),
            # Ensure that the processing stops once a processor successfully
            # processes the message
            (
                3,
                (
                    (False, 'Could not be processed'),
                    (True, 'Processed successfully'),
                ),
                True,
            ),
            # Ensure that when there are no processors, the email is not processed
            (
                0,
                (),
                False,
            ),
        ),
    )
    def test_process_email(self, processor_count, processor_results, email_processed):
        """
        Unit test of _process_email method to ensure that the chain of email
        processing works as expected.
        """
        processor_classes = []
        # Set up our mocked processor classes, ensuring that they return the
        # results we expect
        for i in range(processor_count):
            mocked_processor_class = mock.Mock(spec=EmailProcessor, __name__='')
            mocked_processor = mocked_processor_class.return_value
            try:
                mocked_processor.process_email.return_value = processor_results[i]
            except IndexError:
                continue
            processor_classes.append(mocked_processor_class)
        mailbox = Mailbox(
            'foobar@example.net',
            'foobarbaz1',
            'domain.example.net',
            mail_processor_classes=processor_classes,
        )
        message = mock.Mock()
        processed = mailbox._process_email(message)
        # Ensure that the processing result is as expected
        assert processed == email_processed
        # Ensure that the processor classes were called/not called as specified in
        # processor_results
        for count, processor_class in enumerate(processor_classes):
            processor = processor_class.return_value
            try:
                processor_results[count]
                assert processor.process_email.called_with(message)
            except IndexError:
                assert not processor.process_email.called

    def test_process_email_processing_error(self, caplog):
        """
        Test that _process_email can handle processing errors from a bad email
        processor class.
        """
        processor_classes = []
        for i in range(2):
            mocked_processor_class = mock.Mock(spec=EmailProcessor)
            mocked_processor_class.__name__ = f'Processor {i}'
            mocked_processor = mocked_processor_class.return_value
            mocked_processor.process_email.return_value = (False, 'Bad email')
            processor_classes.append(mocked_processor_class)
        bad_processor = processor_classes[0].return_value

        bad_processor.process_email.side_effect = TypeError('Ooops!')
        uncalled_processor = processor_classes[1].return_value
        mailbox = Mailbox(
            'foobar@example.net',
            'foobarbaz1',
            'domain.example.net',
            mail_processor_classes=processor_classes,
        )
        message = mock.Mock()
        result = mailbox._process_email(message)
        assert result is False
        # Ensure that we failed early and the second processor was not called at all
        assert uncalled_processor.process_email.called is False
        # Ensure that an error message was logged
        expected_error_message = (
            'datahub.email_ingestion.mailbox',
            40,
            f'Error processing email "{message.message_id}" which was processed by '
            'processor "Processor 0"',
        )
        assert expected_error_message in caplog.record_tuples


class TestMailboxHandler:
    """
    Test the MailboxHandler class.
    """

    @override_settings(MAILBOXES=MAILBOXES_SETTING)
    def test_handler_initialisation(self, monkeypatch):
        """
        Functional test to ensure that MailboxHandler is initialised as expected.
        """
        # Mock import_string to avoid import errors for processor_class path strings
        import_string_mock = mock_import_string(monkeypatch)
        mailbox_handler = MailboxHandler()
        mailbox_handler.initialise_mailboxes()
        for mailbox_name, mailbox_config in MAILBOXES_SETTING.items():
            instantiated_mailbox = mailbox_handler.get_mailbox(mailbox_name)
            # ensure that the Mailbox object has the expected attributes
            assert instantiated_mailbox.username == mailbox_config['username']
            assert instantiated_mailbox.password == mailbox_config['password']
            assert instantiated_mailbox.imap_domain == mailbox_config['imap_domain']
            # ensure that the processor class paths were imported
            for processor_class_path in mailbox_config['processor_classes']:
                import_string_mock.assert_any_call(processor_class_path)
            for processor_class in instantiated_mailbox.processor_classes:
                assert processor_class == import_string_mock.return_value
        all_mailboxes = mailbox_handler.get_all_mailboxes()
        assert len(all_mailboxes) == len(MAILBOXES_SETTING.values())

    @override_settings(MAILBOXES=BAD_MAILBOXES_SETTING)
    def test_handler_initialisation_badly_configured(self):
        """
        Functional test to ensure that MailboxHandler raises the correct error
        when badly configured.
        """
        with pytest.raises(ImproperlyConfigured):
            mailbox_handler = MailboxHandler()
            mailbox_handler.initialise_mailboxes()

    @override_settings(MAILBOXES={})
    def test_handler_initialisation_no_mailboxes(self):
        """
        Functional test to ensure that MailboxHandler works as expected when
        there are no mailboxes in the application settings.
        """
        mailbox_handler = MailboxHandler()
        mailbox_handler.initialise_mailboxes()
        assert mailbox_handler.get_all_mailboxes() == []
