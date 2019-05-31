from django.apps import AppConfig


class EmailIngestionConfig(AppConfig):
    name = 'datahub.email_ingestion'

    def ready(self):
        from datahub.email_ingestion import mailbox_handler
        mailbox_handler.initialise_mailboxes()
