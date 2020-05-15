from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.timezone import now

from datahub.user_event_log.constants import UserEventType


class UserEvent(models.Model):
    """
    User event.

    Used to keep a record of specific events that have occurred while the user was using the
    system (e.g. the user exported data from search).

    Not intended as a replacement for logging, but for cases where we need to record data in a
    more structured fashion and retain it for a longer period of time.
    """

    id = models.BigAutoField(primary_key=True)
    # Note: This does not use auto_add_now=True so that the timestamp can be
    # overridden if needed
    timestamp = models.DateTimeField(db_index=True, default=now, editable=False)
    adviser = models.ForeignKey(
        'company.Advisor',
        on_delete=models.CASCADE,
        related_name='user_events',
    )
    type = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=UserEventType.choices,
    )
    api_url_path = models.CharField(
        blank=True,
        verbose_name='API URL path',
        max_length=5000,
        db_index=True,
    )
    data = JSONField(null=True, encoder=DjangoJSONEncoder)

    def __str__(self):
        """Human-friendly string representation."""
        return f'{self.timestamp} – {self.adviser} – {self.get_type_display()}'

    class Meta:
        indexes = [
            models.Index(fields=['api_url_path', 'timestamp']),
            models.Index(fields=['type', 'adviser']),
            models.Index(fields=['timestamp', 'type', 'adviser']),
        ]
        ordering = ('-timestamp', '-pk')
