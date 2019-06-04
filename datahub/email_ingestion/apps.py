from django.apps import AppConfig


class EmailIngestionConfig(AppConfig):
    """
    App config for email_ingestion app.  This ensures that the package's mailbox_handler
    singleton is only initialised when Django's apps are ready; often the email
    processor classes that it instantiates will depend on Django models etc.
    """

    name = 'datahub.email_ingestion'

    def ready(self):
        """
        Initialises the mailbox_handler singleton.
        """
        from datahub.email_ingestion import mailbox_handler
        mailbox_handler.initialise_mailboxes()
