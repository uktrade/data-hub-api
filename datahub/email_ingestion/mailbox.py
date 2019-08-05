import imaplib
from contextlib import contextmanager
from email.errors import MessageParseError
from logging import getLogger

import mailparser
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from mailparser.exceptions import MailParserError

logger = getLogger(__name__)


class EmailRetrievalError(Exception):
    """
    Custom exception for when an email was not successfully retrieved from the
    IMAP server.
    """

    pass


class Mailbox:
    """
    The Mailbox class acts as a gateway to an email inbox - accessed via IMAP.
    It offers methods for getting new messages from the inbox and processing
    them using associated processing classes.

    When an email is retrieved from the inbox successfully, it is marked as
    SEEN on the upstream IMAP inbox.  This is the mechanism we use to ensure
    that emails are only ever processed once.

    The first processor to successfully consume and process the message will stop
    the chain.  Processors will be called in order - so ordering of
    `mail_processor_classes` is important.

    **Important** Any calling code which attempts to get/process new mail using
    a Mailbox should firstly acquire a lock using django_pglocks' advisory_lock mechanism.
    e.g.

    ```
    from django_pglocks import advisory_lock

    with advisory_lock('ingest_emails', wait=False) as acquired:
        if not acquired:
            logger.info('Emails are already being ingested by something else')
            return
        mailbox.process_new_mail()
    ```

    """

    def __init__(
        self,
        username,
        password,
        imap_domain,
        mail_processor_classes,
        imap_port=None,
    ):
        """
        Initialise a Mailbox object.

        :param username: string - the username of the inbox
        :param password: string - the password for the inbox
        :param imap_domain: string - the domain of the imap server to connect to
        :param mail_processor_classes: iterable - EmailProcessor classes which
            should be used to process incoming mail to this mailbox
        :param imap_port: optional int - the port to use when connecting with imap
        """
        self.username = username
        self.password = password
        self.imap_domain = imap_domain
        if imap_port:
            self.imap_port = imap_port
        else:
            self.imap_port = 993
        # Make a copy of the processor class iterable
        self.processor_classes = [processor_class for processor_class in mail_processor_classes]

    @contextmanager
    def _connect(self):
        """
        Connect to the email inbox over IMAP.  The connection is closed down
        automatically when execution leaves the scope of the context.

        :yields: An active imaplib server connection object.
        """
        connection = imaplib.IMAP4_SSL(self.imap_domain, self.imap_port)
        connection.login(self.username, self.password)
        connection.select()
        try:
            yield connection
        finally:
            connection.close()
            connection.logout()

    def _get_all_message_ids(self, connection):
        """
        Fetch all of the message ids that are present in the inbox.

        :param connection: imaplib connection object - the active connection to
            use to retrieve message ids from

        :returns: A list of message id strings.
        """
        # Fetch all the message uids
        response, message_ids = connection.uid('search', None, '(UNSEEN)')
        message_id_string = message_ids[0].strip()
        # Usually `message_id_string` will be a list of space-separated
        # ids; we must make sure that it isn't an empty string before
        # splitting into individual UIDs.
        if message_id_string:
            return message_id_string.decode().split(' ')
        return []

    def _process_email(self, message):
        """
        Run through the EmailProcessor objects associated with this Mailbox and
        attempt to process the message.

        The message will be processed by at most one processor; EmailProcessor
        objects will be called in the order that they were passed in on
        Mailbox instantiation. The method returns as soon as the message has been
        successfully processed by a processor.

        :param message: mailparser.Mailparser object - the message to process

        :returns: True if the message was processed, False otherwise.
        """
        for processor_class in self.processor_classes:
            processor = processor_class()
            processor_name = processor_class.__name__
            try:
                processed, processing_output = processor.process_email(message)
            except Exception:
                error_message = (
                    f'Error processing email "{message.message_id}" '
                    f'which was processed by processor "{processor_name}"'
                )
                logger.exception(error_message)
                return False
            if processed:
                success_message = (
                    f'Email {message.message_id} was processed by processor: '
                    f'{processor_name}'
                )
                logger.info(success_message)
                return True
            logger.debug(
                f'Email {message.message_id} could not be processed by {processor_name}. '
                f'Reason: "{processing_output}"',
            )
        return False

    def _parse_message(self, message_bytes):
        return mailparser.parse_from_bytes(message_bytes)

    def _get_message(self, uid, connection):
        try:
            typ, msg_contents = connection.uid('fetch', uid, '(RFC822)')
        except TypeError as exc:
            # This may happen if something deletes the
            # message between our generating the ID list and our
            # processing it here.
            raise EmailRetrievalError() from exc
        if not msg_contents:
            return None
        message = self._parse_message(msg_contents[0][1])
        return message

    def get_new_mail(self):
        """
        Generator method which gets new messages from the email inbox. After a
        message has been yielded (or an error has been logged while parsing it),
        it is flagged as SEEN on the inbox so that it will not be ingested again later.
        We only consider messages that have not been seen for ingestion.

        :yields: A mailparser.Message object for each parsed message.
        """
        with self._connect() as connection:
            message_ids = self._get_all_message_ids(connection)
            if not message_ids:
                # No new messages to ingest
                return

            for uid in message_ids:
                try:
                    message = self._get_message(uid, connection)
                except (MessageParseError, MailParserError):
                    # If we have some problem parsing the email, it's likely
                    # to be spam/malicious so skip it
                    error_message = (
                        f'Mailbox "{self.username}" failed to parse message'
                    )
                    logger.exception(error_message)
                    # Just set the message to None so that we still mark it as
                    # read later
                    message = None
                except EmailRetrievalError:
                    # We should fail and exit immediately in this case, as it's
                    # probable that another process is processing the inbox
                    error_message = (
                        f'Mailbox "{self.username}" could not retrieve message {uid} successfully'
                    )
                    logger.exception(error_message)
                    return
                if message:
                    yield message

                # Mark the email as read in the inbox
                connection.uid('store', uid, '+FLAGS', '(\\SEEN)')

    def process_new_mail(self):
        """
        Gets all of the new mail in the inbox and goes through the associated
        EmailProcessor classes to process each message.
        """
        messages = self.get_new_mail()
        for message in messages:
            self._process_email(message)


class MailboxHandler:
    """
    Handles all of the mailboxes that are active in our application. This is a
    singleton and should be considered the single gateway for accessing IMAP
    Mailboxes.

    **Important** Any calling code which attempts to get/process new mail using
    a Mailbox should firstly acquire a lock using django_pglocks' advisory_lock mechanism.
    e.g.

    ```
    from django_pglocks import advisory_lock

    with advisory_lock('ingest_emails', wait=False) as acquired:
        if not acquired:
            logger.info('Emails are already being ingested by something else')
            return
        mailbox.process_new_mail()
    ```

    """

    def __init__(self):
        """
        Initialise the MailboxHandler object.
        """
        self.mailboxes = {}

    def initialise_mailboxes(self):
        """
        Initialise all of the mailboxes detailed in the MAILBOXES django setting.
        """
        for mailbox_name, config in settings.MAILBOXES.items():
            properly_configured = config.keys() >= {'username', 'password', 'imap_domain'}
            if not properly_configured:
                message = f'Mailbox "{mailbox_name}" was not configured properly in settings'
                raise ImproperlyConfigured(message)
            processor_class_paths = config.get('processor_classes', [])
            processor_classes = []
            for processor_class_path in processor_class_paths:
                processor_class = import_string(processor_class_path)
                processor_classes.append(processor_class)
            mailbox = Mailbox(
                config['username'],
                config['password'],
                config['imap_domain'],
                processor_classes,
            )
            self.mailboxes[mailbox_name] = mailbox

    def get_all_mailboxes(self):
        """
        Get all active Mailbox objects in a list.
        """
        return list(self.mailboxes.values())

    def get_mailbox(self, identifier):
        """
        Get a single Mailbox object for the specified identifier.

        :param identifier: string - the name of the mailbox to get

        :returns: A Mailbox object.
        """
        return self.mailboxes[identifier]
