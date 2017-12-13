from rest_framework.permissions import BasePermission


class SearchAppPermissions(BasePermission):
    """
    Check the permission_required on view against User Permissions
    """

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted `False` otherwise.
        Raises ImproperlyConfigured if permission_required is not set on view
        """
        user = request.user
        permissions = view.search_app.permission_required

        return user and any(user.has_perm(permission) for permission in permissions)
