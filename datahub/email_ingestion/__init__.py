"""
Generic functionality for processing emails from a mail server.

This is used by datahub.interaction.email_processors for creating DIT interactions from
calendar invitations.
"""

from datahub.email_ingestion.mailbox import MailboxHandler

mailbox_handler = MailboxHandler()
