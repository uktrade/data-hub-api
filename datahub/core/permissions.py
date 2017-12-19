from abc import ABC, abstractmethod

from rest_framework.permissions import BasePermission, DjangoModelPermissions


# View to model action mapping for standard model-based views
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
    'metadata': 'read',
}


# View to model action mapping for many-to-many views where permissions are based on the
# primary model e.g. for InvestmentProjectTeamMember where permissions are based on
# InvestmentProject
_MANY_TO_MANY_VIEW_TO_ACTION_MAPPING = {
    'create': 'change',
    'list': 'read',
    'retrieve': 'read',
    'destroy': 'change',
    'destroy_all': 'change',
    'partial_update': 'change',
    'metadata': 'read',
}


class DjangoCrudPermission(DjangoModelPermissions):
    """Extension of Permission class to include read permissions"""

    perms_map = DjangoModelPermissions.perms_map.copy()
    perms_map['GET'].append('%(app_label)s.read_%(model_name)s')


class ObjectAssociationCheckerBase(ABC):
    """
    Base class for object association checkers.

    Derived classes are used to determine whether a user is associated with a particular object,
    and whether access to a particular object for the current request should be restricted to
    users associated with the object.

    For example, this is used with investment projects to restrict certain third-party
    organisations so that they can only access projects they are associated with.
    """

    @abstractmethod
    def is_associated(self, request, obj) -> bool:
        """Checks whether the user is associated with a particular object."""

    @abstractmethod
    def should_apply_restrictions(self, request, view_action, model) -> bool:
        """
        Checks whether a request should be restricted to objects that the user is associated with.
        """


class IsAssociatedToObjectPermission(BasePermission):
    """
    DRF permission class that checks if an object is associated to the user.

    To use, derive from this class and override the checker_class class attribute. It should
    point at a class derived from ObjectAssociationCheckerBase.
    """

    checker_class = None

    def __init__(self):
        """Initialises the instance."""
        self.checker = self.checker_class()

    def get_actual_object(self, obj):
        """
        Gets the actual object for permissions to be checked on.

        Subclasses can override this for cases where permissions need to be checked on an
        attribute on the model associated with the view's queryset.
        """
        return obj

    def has_object_permission(self, request, view, obj):
        """
        Determines whether the user has permission for the specified object, using checker_class.
        """
        actual_obj = self.get_actual_object(obj)

        return self._check_actual_object_permission(request, view, actual_obj)

    def _check_actual_object_permission(self, request, view, obj):
        if self.checker.should_apply_restrictions(request, view.action, obj._meta.model):
            return self.checker.is_associated(request, obj)
        return True


def get_model_action_for_view_action(http_method, view_action, many_to_many=False):
    """Gets the model action corresponding to a view action."""
    if http_method == 'OPTIONS':
        return 'read'

    mapping = _MANY_TO_MANY_VIEW_TO_ACTION_MAPPING if many_to_many else _VIEW_TO_ACTION_MAPPING

    return mapping[view_action]
