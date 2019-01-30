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


def _default_value_for_nullable_with_callable_default():
    return 'default value'


class NullableWithDefaultModel(models.Model):
    """Model that has a nullable field with a default value."""

    nullable_with_default = models.BooleanField(null=True, default=True)
    nullable_with_callable_default = models.CharField(
        null=True,
        max_length=255,
        default=_default_value_for_nullable_with_callable_default,
    )
    nullable_without_default = models.BooleanField(null=True)
    non_nullable_with_default = models.BooleanField(default=True)


class ForeignAndM2MModel(models.Model):
    """Model with both a foreign key and many-to-many field with the same target model."""

    value = models.ForeignKey(
        MetadataModel,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='+',
    )
    values = models.ManyToManyField(MetadataModel, blank=True, related_name='+')


class Person(models.Model):
    """Person model."""

    first_name = models.TextField()
    last_name = models.TextField()
    country = models.TextField(null=True, blank=True)


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
