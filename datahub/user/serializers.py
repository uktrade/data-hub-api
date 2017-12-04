from rest_framework import serializers

from datahub.company.models.adviser import Advisor


class WhoAmISerializer(serializers.ModelSerializer):
    """Adviser serializer for that includes a permissions"""

    permissions = serializers.SerializerMethodField()

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
        """Serialize permissions into simplified structure."""
        formatted_permissions = {}
        for perm in obj.get_all_permissions():
            _, action_model = perm.split('.', 1)
            action, model = action_model.split('_', 1)

            model_dict = formatted_permissions.setdefault(model, {})
            model_dict[action] = True

        return formatted_permissions
