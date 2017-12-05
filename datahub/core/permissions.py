from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import BasePermission, DjangoModelPermissions


_VIEW_TO_ACTION_MAPPING = {
    'create': 'add',
    'list': 'read',
    'detail': 'read',
    'retrieve': 'read',
    'destroy': 'delete',
    'destroy_all': 'delete',
    'partial_update': 'change',
    'archive': 'change',
    'unarchive': 'change',
}


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


class ObjectAssociationCheckerBase:
    """Base association check class."""

    def is_associated(self, request, view, obj):
        """Check for connection."""
        return True

    def should_apply_restrictions(self, request, view):
        """Check if restrictions should be applied."""
        return False


class IsAssociatedToObjectPermission(BasePermission, ObjectAssociationCheckerBase):
    """Permission that checks if an object is associated to the user"""

    base_permission = None

    def has_object_permission(self, request, view, obj):
        """Check for object permissions."""
        if self.should_apply_restrictions(request, view):
            return self.is_associated(request, view, obj)
        return True


def get_model_action_for_view_action(method):
    """Gets the model action corresponding to a view action."""
    return _VIEW_TO_ACTION_MAPPING[method]
