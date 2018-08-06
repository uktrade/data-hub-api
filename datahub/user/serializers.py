import re

from rest_framework import serializers

from datahub.company.models.adviser import Advisor
from datahub.metadata.serializers import TeamSerializer


VIEW_PERMISSION_REGEX = re.compile(r'^([^.]*\.)view(_.*)$')


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
        """
        Get all of the user's permissions.

        To keep backwards compatibility, permissions with codenames that start with view_ are
        replicated as permissions with codenames that start with read_. (Once the front end has
        been updated to use the new view_ permissions, this replication can be removed.)
        """
        permissions = obj.get_all_permissions()
        view_permissions_subs = (
            VIEW_PERMISSION_REGEX.subn(r'\1read\2', permission) for permission in permissions
        )
        read_permissions = {
            permission for permission, sub_count in view_permissions_subs if sub_count > 0
        }
        return permissions | read_permissions
