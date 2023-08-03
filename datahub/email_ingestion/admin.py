from django.contrib import admin

from datahub.email_ingestion.models import MailboxLogging


@admin.register(MailboxLogging)
class MailboxLoggingAdmin(admin.ModelAdmin):
    """Mailbox Logging admin."""

    raw_id_fields = ('interaction',)
