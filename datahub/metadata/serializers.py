from datahub.core.serializers import ConstantModelSerializer, NestedRelatedField

from .models import Country, TeamRole, UKRegion


class TeamSerializer(ConstantModelSerializer):
    """Team serializer."""

    role = NestedRelatedField(TeamRole, read_only=True)
    uk_region = NestedRelatedField(UKRegion, read_only=True)
    country = NestedRelatedField(Country, read_only=True)
