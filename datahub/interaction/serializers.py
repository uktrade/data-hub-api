from rest_framework import serializers

from datahub.company.serializers import AdviserSerializer
from datahub.core.validate_utils import AnyOfValidator, RequiredUnlessAlreadyBlank
from .models import Interaction


class InteractionSerializerRead(serializers.ModelSerializer):
    """Interaction Serializer."""

    dit_adviser = AdviserSerializer()

    class Meta:  # noqa: D101
        model = Interaction
        depth = 2
        fields = '__all__'


class InteractionSerializerWrite(serializers.ModelSerializer):
    """Interaction Serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Interaction
        fields = '__all__'
        validators = [
            AnyOfValidator('company', 'investment_project'),
            RequiredUnlessAlreadyBlank('dit_team', 'interaction_type', 'service')
        ]
