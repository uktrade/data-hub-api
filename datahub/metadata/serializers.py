from functools import partial

from rest_framework import serializers

from datahub.core.serializers import ConstantModelSerializer, NestedRelatedField
from .models import Country, Service, TeamRole, UKRegion


TeamWithGeographyField = partial(
    NestedRelatedField,
    'metadata.Team',
    extra_fields=(
        'name',
        ('uk_region', NestedRelatedField(UKRegion, read_only=True)),
        ('country', NestedRelatedField(Country, read_only=True)),
    ),
)


class ServiceSerializer(ConstantModelSerializer):
    """Service serializer."""

    contexts = serializers.MultipleChoiceField(choices=Service.CONTEXTS, read_only=True)


class TeamSerializer(ConstantModelSerializer):
    """Team serializer."""

    role = NestedRelatedField(TeamRole, read_only=True)
    uk_region = NestedRelatedField(UKRegion, read_only=True)
    country = NestedRelatedField(Country, read_only=True)


class SectorSerializer(serializers.Serializer):
    """Sector serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    segment = serializers.ReadOnlyField()
    parent = NestedRelatedField('metadata.Sector', read_only=True)
    level = serializers.ReadOnlyField()
    disabled_on = serializers.ReadOnlyField()
