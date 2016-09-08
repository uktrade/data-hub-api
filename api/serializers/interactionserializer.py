from rest_framework import serializers
from api.models.interaction import Interaction


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = (
            'id',
            'interaction_type',
            'subject',
            'date_of_interaction',
            'advisor',
            'notes',
            'company'
        )
