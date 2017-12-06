from rest_framework import serializers

from datahub.company.models.adviser import Advisor
from datahub.metadata.serializers import TeamSerializer


class WhoAmISerializer(serializers.ModelSerializer):
    """Adviser serializer for that includes a permissions"""

    permissions = serializers.SerializerMethodField()
    dit_team = TeamSerializer(read_only=True)

    class Meta:
        model = Advisor
        fields = (
            'id',
            'name',
            'last_login',
            'first_name',
            'last_name',
            'email',
            'contact_email',
            'telephone_number',
            'dit_team',
            'permissions',
        )
        depth = 2

    def get_permissions(self, obj):
        """Serialize permissions."""
        return obj.get_all_permissions()
