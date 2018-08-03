from django.db import models

from ...models import BaseConstantModel, BaseModel, DisableableModel


class MetadataModel(BaseConstantModel):
    """Test metadata model."""


class InheritedModel(BaseModel):
    """
    Simple model extending BaseModel.
    This is to test the inherited fields.
    """


class EmptyModel(models.Model):
    """
    Empty Django model.
    This is not going to have any fields apart from id.
    """


class MyDisableableModel(DisableableModel):
    """Simple DisableableModel."""


class PermissionModel(models.Model):
    """Simple Model with Permission"""
