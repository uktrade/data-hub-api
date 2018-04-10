from django.conf import settings
from django.db import models

from datahub.core.models import BaseConstantModel, BaseModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class FeatureFlag(BaseConstantModel, BaseModel):
    """Feature flag.

    It keeps the status of features - whether one is enabled or disabled.
    """

    description = models.TextField(blank=True)
