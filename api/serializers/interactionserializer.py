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
            'company',
            'contact',
            'created_date',
            'modified_date',
        )
        depth = 1


class InteractionSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = (
            'id',
            'interaction_type',
            'subject',
            'date_of_interaction',
            'advisor',
            'notes',
            'company',
            'contact',
        )
