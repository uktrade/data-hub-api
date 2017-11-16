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


class UserObjectAssociationCheck:
    """Base association check class."""

    _action2method = {
        'list': 'read',
        'detail': 'read',
        'retrieve': 'read',
        'destroy': 'delete',
        'destroy_all': 'delete',
        'partial_update': 'change',
    }

    def action_2_method(self, action):
        """Change ViewSet action to permissions method."""
        return self._action2method.get(action, action)

    def is_associated(self, request, view, obj):
        """Check for connection."""
        return True

    def check_condition(self, request, view):
        """Check if condition should be applied."""
        return

    class Meta:
        abstract = True


class IsAssociatedToObjectPermission(BasePermission, UserObjectAssociationCheck):
    """
    Check the investment project has a users team associated with it
    """

    base_permission = None

    def has_object_permission(self, request, view, obj):
        """Check for object permissions."""
        if self.check_condition(request, view):
            return self.is_associated(request, view, obj)
        return True
