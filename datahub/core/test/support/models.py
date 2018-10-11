from django.db import models

from datahub.core.models import BaseConstantModel, BaseModel, DisableableModel


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
    """Simple Model with Permission."""


class Person(models.Model):
    """Person model."""

    first_name = models.TextField()
    last_name = models.TextField()


class Book(models.Model):
    """Book model."""

    GENRES = (
        ('horror', 'Horror'),
        ('non_fiction', 'Non-fiction'),
    )

    name = models.TextField()
    proofreader = models.ForeignKey(
        Person,
        null=True,
        related_name='proofread_books',
        on_delete=models.CASCADE,
    )
    authors = models.ManyToManyField(Person, related_name='books')
    published_on = models.DateField()
    genre = models.CharField(null=True, max_length=255, choices=GENRES)

    def __str__(self):
        """Human-friendly string representation."""
        return self.name
