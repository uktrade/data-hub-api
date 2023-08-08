import uuid

from django.conf import settings
from django.db import models


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class MailboxProcessingStatus(models.TextChoices):
    RETRIEVED = ('retrieved', 'Retrieved')
    PROCESSED = ('processed', 'Processed')
    FAILURE = ('failure', 'Failure')

    UNKNOWN = ('unknown', 'Unknown')


class MailboxLogging(models.Model):
    """
    Model for mailbox logging.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    content = models.TextField()

    retrieved_on = models.DateTimeField()

    interaction = models.ForeignKey(
        'interaction.Interaction',
        on_delete=models.CASCADE,
        related_name='mailbox',
        null=True,
        blank=True,
    )
    source = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)

    status = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=MailboxProcessingStatus.choices,
        default=MailboxProcessingStatus.UNKNOWN,
    )
    extra = models.TextField(blank=True)

    def __str__(self):
        return f'Email: {self.adviser}'
