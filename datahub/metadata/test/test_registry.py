import pytest
from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers

from datahub.core.serializers import ConstantModelSerializer
from datahub.metadata.models import Sector, UKRegion
from datahub.metadata.registry import MetadataRegistry

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_register_with_defaults():
    """Tests the default values."""
    reg = MetadataRegistry()

    reg.register('sector', model=Sector)
    reg.register('uk-region', model=UKRegion)

    assert set(reg.mappings) == {'sector', 'uk-region'}

    mapping = reg.mappings['sector']
    assert mapping.model is Sector
    assert mapping.queryset is not None
    assert mapping.serializer == ConstantModelSerializer


def test_register_with_overriding_values():
    """Tests the values overridden."""
    class MySerializer(serializers.Serializer):
        """Used as overridden serializer"""

    reg = MetadataRegistry()

    reg.register('sector', model=Sector, queryset=Sector.objects.none, serializer=MySerializer)

    mapping = reg.mappings['sector']
    assert mapping.model is Sector
    assert mapping.queryset == Sector.objects.none
    assert mapping.serializer == MySerializer


def test_register_id_already_used():
    """
    Tests that if I try to register the same metadata twice, the second call fails.
    """
    reg = MetadataRegistry()

    reg.register('sector', model=Sector)

    with pytest.raises(ImproperlyConfigured):
        reg.register('sector', model=UKRegion)

    assert set(reg.mappings) == {'sector'}
