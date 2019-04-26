import imaplib
from contextlib import contextmanager
from email.errors import MessageParseError
from logging import getLogger

import mailparser
from mailparser.exceptions import MailParserError

logger = getLogger(__name__)


class Mailbox:
    """
    The Mailbox class acts as a gateway to an email inbox - accessed via IMAP.
    It offers methods for getting new messages from the inbox and processing
    them using associated processing classes.

    When an email is retrieved from the inbox successfully, it is marked as
    deleted on the upstream IMAP inbox.  This is the mechanism we use to ensure
    that emails are only ever processed once.

    The first processor to successfully consume and process the message will stop
    the chain.  Processors will be called in order - so ordering of
    `mail_processor_classes` is important.
    """

    def __init__(
        self,
        email,
        password,
        imap_domain,
        mail_processor_classes,
        imap_port=None,
        use_ssl=True,
    ):
        """
        Initialise a Mailbox object.

        :param email: string - the email address of the inbox
        :param password: string - the password for the inbox
        :param imap_domain: string - the domain of the imap server to connect to
        :param mail_processor_classes: iterable - EmailProcessor classes which
            should be used to process incoming mail to this mailbox
        :param imap_port: optional int - the port to use when connecting with imap
        :param use_ssl: optional boolean - whether or not to use SSL with imap, defaults
            to True
        """
        self.email = email
        self.password = password
        self.imap_domain = imap_domain
        if imap_port:
            self.imap_port = imap_port
        else:
            if use_ssl:
                self.imap_port = 993
            else:
                self.imap_port = 465
        self.use_ssl = use_ssl
        # Make a copy of the processor class iterable
        self.processor_classes = [processor_class for processor_class in mail_processor_classes]

    @contextmanager
    def _connect(self):
        """
        Connect to the email inbox over IMAP.  The connection is closed down
        automatically when execution leaves the scope of the context.

        :yields: An active imaplib server connection object.
        """
        transport = imaplib.IMAP4_SSL
        if not self.use_ssl:
            transport = imaplib.IMAP4
        server = transport(self.imap_domain, self.imap_port)
        server.login(self.email, self.password)
        server.select()
        try:
            yield server
        finally:
            server.close()
            server.logout()

    def _get_all_message_ids(self, server):
        """
        Fetch all of the message ids that are present in the inbox.

        :param server: imaplib connection object - the active connection to
            use to retrieve message ids from

        :returns: A list of message id strings.
        """
        # Fetch all the message uids
        response, message_ids = server.uid('search', None, 'ALL')
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
            processed, message = processor.process_email(message)
            if processed:
                processor_name = processor_class.__name__
                message = f'Email {message} was processed by processor: {processor_name}'
                logger.info(message)
                return True
        return False

    def _parse_message(self, message_bytes):
        return mailparser.parse_from_bytes(message_bytes)

    def get_new_mail(self):
        """
        Generator method which gets new messages from the email inbox. After a
        message has been yielded, it is flagged as deleted on the inbox so that
        it will not be ingested again later.

        :yields: A mailparser.Message object for each parsed message.
        """
        with self._connect() as server:
            message_ids = self._get_all_message_ids(server)
            if not message_ids:
                # No new messages to ingest
                return

            for uid in message_ids:
                try:
                    typ, msg_contents = server.uid('fetch', uid, '(RFC822)')
                    if not msg_contents:
                        continue
                    try:
                        message = self._parse_message(msg_contents[0][1])
                    except TypeError:
                        # This may happen if another thread/process deletes the
                        # message between our generating the ID list and our
                        # processing it here.
                        raise
                    yield message
                except (MessageParseError, MailParserError):
                    # If we have some problem parsing the email, it's likely
                    # to be spam/malicious so skip it
                    continue

                # Mark the email for deletion in the inbox
                server.uid('store', uid, '+FLAGS', '(\\Deleted)')
            # Carry out deletion for the emails marked for deletion
            server.expunge()

    def process_new_mail(self):
        """
        Gets all of the new mail in the inbox and goes through the associated
        EmailProcessor classes to process each message.
        """
        messages = self.get_new_mail()
        for message in messages:
            self._process_email(message)
