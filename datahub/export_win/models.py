from datahub.core.models import BaseOrderedConstantModel
from django.db import models
from django.conf import settings

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BaseExportWinOrderedConstantModel(BaseOrderedConstantModel):
    """Base class for an Export Win."""

    export_win_id = models.CharField(
        max_length=MAX_LENGTH,
    )


class TeamType(BaseExportWinOrderedConstantModel):
    """Team type (for export wins)."""
