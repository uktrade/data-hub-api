from rest_framework import serializers

from datahub.company.models.adviser import Advisor


class WhoAmISerializer(serializers.ModelSerializer):
    """Adviser serializer for that includes a permissions"""

    name = serializers.CharField()

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
        )
        depth = 2

    def serialize_permissions(self, permissions):
        """Serialize permissions into simplified structure."""
        formatted_permissions = {}
        for perm in permissions:
            app, action_model = perm.split('.', 1)
            action, model = action_model.split('_', 1)

            if model in formatted_permissions:
                formatted_permissions[model].append(action)
            else:
                formatted_permissions[model] = [action]

        return formatted_permissions

    @property
    def data(self):
        """Data property."""
        ret = super().data
        ret['permissions'] = self.serialize_permissions(self.instance.get_all_permissions())

        return ret
