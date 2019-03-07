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


@pytest.mark.parametrize(
    'metadata_id,path_prefix,expected_mapping',
    (
        ('sector', None, 'sector'),
        ('sector', 'investments', 'investments/sector'),
    ),
)
def test_register_id_already_used(metadata_id, path_prefix, expected_mapping):
    """
    Tests that if I try to register the same metadata twice, the second call fails.
    """
    reg = MetadataRegistry()

    reg.register(metadata_id, model=Sector, path_prefix=path_prefix)

    with pytest.raises(ImproperlyConfigured):
        reg.register(metadata_id, model=UKRegion, path_prefix=path_prefix)

    assert set(reg.mappings) == {expected_mapping}


def test_register_with_path_prefix():
    """
    Tests registering with a prefix to url path

    """
    reg = MetadataRegistry()

    reg.register('sector', model=Sector, path_prefix='investment')
    mapping = reg.mappings['investment/sector']
    assert mapping.model is Sector
