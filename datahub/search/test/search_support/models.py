from django.db import models

from datahub.core.models import BaseModel


class SimpleModel(BaseModel):
    """
    Simple model extending BaseModel.
    """

    name = models.CharField(max_length=500)
    country = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=500, blank=True)
    date = models.DateField(null=True)


class RelatedModel(BaseModel):
    """A model related to SimpleModel."""

    simpleton = models.ForeignKey(SimpleModel, null=True, blank=True, on_delete=models.CASCADE)
