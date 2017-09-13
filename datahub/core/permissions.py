from rest_framework.permissions import BasePermission


class AnyOfChainer(BasePermission):
    """Chains DRF permission classes using an or operator."""

    def __init__(self, *args):
        """Initialises the instance with a list of permission classes."""
        self.classes = args

    def __call__(self):
        """Returns self, for compatibility with DRF."""
        return self

    def has_permission(self, request, view):
        """
        Checks if the user has permissions for a view according to any of the permission
        classes.
        """
        return any(perm_class().has_permission(request, view) for perm_class in self.classes)

    def has_object_permission(self, request, view, obj):
        """
        Checks if the user has permissions for an object according to any of the permission
        classes.
        """
        return any(perm_class().has_object_permission(request, view, obj) for perm_class in
                   self.classes)
