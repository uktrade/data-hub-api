import imaplib
import mailparser
from logging import getLogger

from django.conf import settings
from django.utils.module_loading import import_string

from email.errors import MessageParseError

logger = getLogger(__name__)


class Mailbox:

    def __init__(
        self,
        email,
        password,
        imap_domain,
        mail_processor_classes,
        imap_port=None,
        use_ssl=True
    ):
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
        self.processors = []
        for processor_class_path in mail_processor_classes:
            processor_class = import_string(processor_class_path)
            self.processors.append(processor_class())

    def connect(self):
        transport = imaplib.IMAP4_SSL
        if not self.use_ssl:
            transport = imaplib.IMAP4
        self.server = transport(self.imap_domain, self.imap_port)
        self.server.login(self.email, self.password)
        self.server.select()

    def _get_all_message_ids(self):
        # Fetch all the message uids
        response, message_ids = self.server.uid('search', None, 'ALL')
        message_id_string = message_ids[0].strip()
        # Usually `message_id_string` will be a list of space-separated
        # ids; we must make sure that it isn't an empty string before
        # splitting into individual UIDs.
        if message_id_string:
            return message_id_string.decode().split(' ')
        return []

    def _process_email(self, message):
        for processor in self.processors:
            processed, message = processor.process_email(message)
            logger.info("Processed: %s Message: %s" % (processed, message))
            if processed:
                break

    def get_new_mail(self):
        self.connect()
        message_ids = self._get_all_message_ids()

        if not message_ids:
            return

        for uid in message_ids:
            try:
                typ, msg_contents = self.server.uid('fetch', uid, '(RFC822)')
                if not msg_contents:
                    continue
                try:
                    message = mailparser.parse_from_bytes(msg_contents[0][1])
                except TypeError:
                    # This happens if another thread/process deletes the
                    # message between our generating the ID list and our
                    # processing it here.
                    continue

                yield message
            except MessageParseError:
                continue

            self.server.uid('store', uid, "+FLAGS", "(\\Deleted)")
        self.server.expunge()
        return

    def process_new_mail(self):
        messages = self.get_new_mail()
        for message in messages:
            logger.info("Attachments:")
            logger.info(message.attachments)
            logger.info("Headers:")
            logger.info(message._message.keys())
            logger.info(dir(message))
            logger.info("Subject: %s" % message.subject)
            logger.info("To: %s" % message.to)
            logger.info("From: %s" % message.from_)
            logger.info("CC: %s" % message.cc)
            logger.info("Authentication: %s" % message.authentication_results)
            logger.info("Text-plain:")
            logger.info(message.text_plain)
            logger.info("Text-html:")
            logger.info(message.text_html)
            self._process_email(message)


class MailboxManager:

    def __init__(self):
        self.mailboxes = {}
        self.initialise_mailboxes()

    def initialise_mailboxes(self):
        for mailbox_name, config in settings.MAILBOXES.items():
            if not (config['email'] and config['password'] and config['imap_domain']):
                continue
            processor_classes = config.get('processor_classes', [])
            mailbox = Mailbox(
                config['email'],
                config['password'],
                config['imap_domain'],
                processor_classes,
            )
            self.mailboxes[mailbox_name] = mailbox

    def get_all_mailboxes(self):
        return list(self.mailboxes.values())

    def get_mailbox(self, identifier):
        return self.mailboxes[identifier]


mailbox_manager = MailboxManager()
