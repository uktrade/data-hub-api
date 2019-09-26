import logging
from abc import ABC, abstractmethod

from rest_framework.permissions import BasePermission, DjangoModelPermissions

from datahub.core.exceptions import APIMethodNotAllowedException

logger = logging.getLogger(__name__)


# View to model action mapping for standard model-based views
_VIEW_TO_ACTION_MAPPING = {
    'create': 'add',
    'list': 'view',
    'detail': 'view',
    'retrieve': 'view',
    'destroy': 'delete',
    'destroy_all': 'delete',
    'partial_update': 'change',
    'archive': 'change',
    'unarchive': 'change',
    'metadata': 'view',
}


# View to model action mapping for many-to-many views where permissions are based on the
# primary model e.g. for InvestmentProjectTeamMember where permissions are based on
# InvestmentProject
_MANY_TO_MANY_VIEW_TO_ACTION_MAPPING = {
    'create': 'change',
    'list': 'view',
    'retrieve': 'view',
    'destroy': 'change',
    'destroy_all': 'change',
    'partial_update': 'change',
    'replace_all': 'change',
    'metadata': 'view',
}


class DjangoCrudPermission(DjangoModelPermissions):
    """Extension of Permission class to include view permissions"""

    perms_map = {
        **DjangoModelPermissions.perms_map,
        'GET': ['%(app_label)s.view_%(model_name)s'],
    }


class HasPermissions(BasePermission):
    """Simple DRF permission class that checks if the user has all of a set of permissions."""

    def __init__(self, *required_permissions):
        """Initialises the instance with a list of permissions that the user must have."""
        if not required_permissions:
            raise ValueError('At least one permission must be provided.')
        self.required_permissions = required_permissions

    def __call__(self):
        """
        Used for compatibility with DRF.

        (DRF instantiates permission classes, but we use instantiation to configure the class
        here.)
        """
        return self

    def has_permission(self, request, view):
        """Returns whether the user has permission for a view."""
        if not request.user or not request.user.is_authenticated:
            return False

        return all(request.user.has_perm(perm) for perm in self.required_permissions)


class ViewBasedModelPermissions(BasePermission):
    """
    Model-permission-based permission class.

    This differs from the standard DjangoModelPermissions class in that:
    - the permissions mapping is based on view/model actions rather than HTTP methods
    - the user only needs to have one the permissions corresponding to each action, rather than
      all of them
    """

    many_to_many = False
    model = None
    permission_template = '{app_label}.{action}_{model_name}'
    permission_mapping = {
        'add': (
            permission_template,
        ),
        'view': (
            permission_template,
        ),
        'change': (
            permission_template,
        ),
        'delete': (
            permission_template,
        ),
    }

    extra_view_to_action_mapping = None

    def has_permission(self, request, view):
        """Returns whether the user has permission for a view."""
        if not request.user or not request.user.is_authenticated:
            return False

        model = self._get_model(view)
        perms = self._get_required_permissions(request, view, model)

        return any(request.user.has_perm(perm) for perm in perms)

    def _get_required_permissions(self, request, view, model_cls):
        """
        Returns the permissions that a user should have one of for a particular method.
        """
        action = get_model_action_for_view_action(
            request.method,
            view.action,
            many_to_many=self.many_to_many,
            extra_view_to_action_mapping=self.extra_view_to_action_mapping,
        )

        format_kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name,
            'action': action,
        }

        return [perm.format(**format_kwargs) for perm in self.permission_mapping[action]]

    def _get_model(self, view):
        return self.model or view.get_queryset().model


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
    def should_apply_restrictions(self, request, view_action) -> bool:
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
        if self.checker.should_apply_restrictions(request, view.action):
            return obj is not None and self.checker.is_associated(request, obj)
        return True


def get_model_action_for_view_action(
    http_method,
    view_action,
    many_to_many=False,
    extra_view_to_action_mapping=None,
):
    """Gets the model action corresponding to a view action."""
    if http_method == 'OPTIONS':
        return 'view'

    if view_action is None:
        raise APIMethodNotAllowedException()

    mapping = (
        _MANY_TO_MANY_VIEW_TO_ACTION_MAPPING.copy()
        if many_to_many else _VIEW_TO_ACTION_MAPPING.copy()
    )

    if extra_view_to_action_mapping is not None:
        mapping.update(extra_view_to_action_mapping)

    return mapping[view_action]
