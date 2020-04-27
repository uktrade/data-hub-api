from rest_framework.permissions import BasePermission


class SearchPermissions(BasePermission):
    """
    DRF permission class that checks that the user has at least one of the permissions in the
    view_permissions attribute on the search app.
    """

    is_export = False

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted `False` otherwise.
        """
        if not (request.user and request.user.is_authenticated):
            return False

        return has_permissions_for_app(request.user, view.search_app, is_export=self.is_export)


class SearchAndExportPermissions(SearchPermissions):
    """
    DRF permission class that checks that the user has at least one of the permissions in the
    view_permissions attribute (on the search app), and additionally has the permission in
    export_permission attribute (on the search app).
    """

    is_export = True


def has_permissions_for_app(user, search_app, is_export=False):
    """
    Checks if the user has permission to search for records related to a search app.

    This is done by checking if the user has at least one of the permissions in the
    view_permissions attribute on the search app.

    If is_export is True, the user must also have the permission in the export_permission
    attribute on the search app.
    """
    has_view_permission = any(
        user.has_perm(permission) for permission in search_app.view_permissions
    )

    if is_export:
        return has_view_permission and user.has_perm(search_app.export_permission)

    return has_view_permission
