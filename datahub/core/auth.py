from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission


class TeamModelPermissionsBackend(ModelBackend):
    """Extension of CDMSUserBackend to include a team based permissions for user"""

    def _get_team_permissions(self, user_obj):
        """
        This method is called by the ModelBackend _get_permissions() dynamically
        as part of aggregating user, group and team permissions
        """
        if user_obj.dit_team and user_obj.dit_team.role:
            groups = user_obj.dit_team.role.groups.all()
        else:
            groups = []

        return Permission.objects.filter(group__in=groups)

    def get_team_permissions(self, user_obj, obj=None):
        """
        Returns a set of permission strings the user `user_obj` has from the
        teams they belong to based on groups associated to team roles.
        """
        return self._get_permissions(user_obj, obj, 'team')

    def get_all_permissions(self, user_obj, obj=None):
        """
        Because of using cache in the parent class, its hard to extend using super()
        so the code is slightly duplicated
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()
        if not hasattr(user_obj, '_perm_cache'):
            user_obj._perm_cache = self.get_user_permissions(user_obj).copy()
            user_obj._perm_cache.update(self.get_group_permissions(user_obj))
            user_obj._perm_cache.update(self.get_team_permissions(user_obj))
        return user_obj._perm_cache
