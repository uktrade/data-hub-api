from collections import defaultdict
from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import BasePermission, DjangoModelPermissions


class DjangoCrudPermission(DjangoModelPermissions):
    """Extension of Permission class to include read permissions"""

    perms_map = DjangoModelPermissions.perms_map.copy()
    perms_map['GET'].append('%(app_label)s.read_%(model_name)s')


class UserHasPermissions(BasePermission):
    """
    Check the permission_required on view against User Permissions
    """

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted `False` otherwise.
        Raises ImproperlyConfigured if permission_required is not set on view
        """
        if not hasattr(view, 'permission_required'):
            raise ImproperlyConfigured()
        return request.user and request.user.has_perm(view.permission_required)


def serialize_permissions(permissions):
    """
    Serialize permissions into simplified structure
    """
    formatted_permissions = defaultdict(list)
    for perm in permissions:
        app, action_model = perm.split('.', 1)
        action, model = action_model.split('_', 1)

        formatted_permissions[model].append(action)

    return formatted_permissions
