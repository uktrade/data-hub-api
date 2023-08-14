from django.contrib import admin

from datahub.email_ingestion.models import MailboxLogging


@admin.register(MailboxLogging)
class MailboxLoggingAdmin(admin.ModelAdmin):
    """Mailbox Logging admin."""

    list_display = ('id', 'status', 'retrieved_on', 'interaction_id')
    search_fields = ('id', 'content')
    list_filter = ('status',)
    ordering = ('retrieved_on',)

    raw_id_fields = ('interaction',)
