from django.db import models
from django.utils.timezone import now


class BaseModel(models.Model):

    modified_on = models.DateTimeField(default=now, null=True)
    created_on = models.DateTimeField(default=now, null=True)

    class Meta:
        abstract = True


class BaseConstantModel(models.Model):

    id = models.UUIDField(primary_key=True, unique=True)
    name = models.TextField(blank=True)

    class Meta:
        abstract = True
