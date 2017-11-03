from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import BasePermission, DjangoModelPermissions


class DjangoCrudPermission(DjangoModelPermissions):
    """Extension of Permission class to include read permissions"""

    perms_map = DjangoModelPermissions.perms_map
    perms_map['GET'].append('%(app_label)s.read_%(model_name)s')


class UserHasPermissions(BasePermission):
    """
    Check the permission_required on view against User Permissions
    """

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted or there is no
        required_permission set for view, `False` otherwise.
        """
        if not hasattr(view, 'permission_required'):
            raise ImproperlyConfigured()
        return request.user and request.user.has_perm(view.permission_required)
