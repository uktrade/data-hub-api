"""
Generic functionality for processing emails from a mail server.

This is used by datahub.interaction.email_processors for creating DIT interactions from
calendar invitations.
"""

from datahub.email_ingestion.mailbox import MailboxHandler

default_app_config = 'datahub.email_ingestion.apps.EmailIngestionConfig'
mailbox_handler = MailboxHandler()
