import uuid

from django.conf import settings
from django.db import models

from datahub.core import reversion

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class IngestedFile(models.Model):
    """
    Model to track which Company Activity data source files have been ingested already
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    filepath = models.CharField(
        max_length=MAX_LENGTH,
        help_text=(
            'The S3 object path including prefix of the ingested file'
        ),
    )
    created_on = models.DateTimeField(auto_now_add=True)
