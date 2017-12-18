from rest_framework.permissions import BasePermission


class SearchAppPermissions(BasePermission):
    """
    DRF permission class that checks the user has at least one of the permissions in the
    permission_required attribute on the search app.
    """

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted `False` otherwise.
        """
        return has_permissions_for_app(request, view.search_app)


def has_permissions_for_app(request, search_app):
    """
    Checks if the user has permission to search for records related to a search app.

    This is done by checking if the user has at least one of the permissions in the
    permission_required attribute on the search app.
    """
    user = request.user
    permissions = search_app.permission_required

    return user and any(user.has_perm(permission) for permission in permissions)
