from django.db import models

from datahub.core.models import BaseModel


class SimpleModel(BaseModel):
    """
    Simple model extending BaseModel.
    """

    name = models.CharField(max_length=500)
