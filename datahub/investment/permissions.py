from django.db.models.query_utils import Q
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import BasePermission

from datahub.core.permissions import (
    get_model_action_for_view_action,
    IsAssociatedToObjectPermission,
    ObjectAssociationCheckerBase
)
from datahub.core.utils import StrEnum


class Permissions(StrEnum):
    """Permission codename constants."""

    read_all = 'read_all_investmentproject'
    read_associated = 'read_associated_investmentproject'
    change_all = 'change_all_investmentproject'
    change_associated = 'change_associated_investmentproject'
    add = 'add_investmentproject'
    delete = 'delete_investmentproject'


class PermissionTemplates(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated = '{app_label}.{action}_associated_{model_name}'
    standard = '{app_label}.{action}_{model_name}'


class InvestmentProjectModelPermissions(BasePermission):
    """
    Custom permissions class for investment views.

    This differs from the standard DjangoModelPermissions class in that:
    - the permissions mapping is based on view/model actions rather than HTTP methods
    - the user only needs to have one the permissions corresponding to each action, rather than
      all of them
    """

    permission_mapping = {
        'add': (
            PermissionTemplates.standard,
        ),
        'read': (
            PermissionTemplates.all,
            PermissionTemplates.associated,
        ),
        'change': (
            PermissionTemplates.all,
            PermissionTemplates.associated,
        ),
        'delete': (
            PermissionTemplates.standard,
        ),
    }

    def has_permission(self, request, view):
        """Returns whether the user has permission for a view."""
        if not request.user or not request.user.is_authenticated:
            return False

        model = _get_model_for_view(view)
        perms = self._get_required_permissions(request, view, model)

        return any(request.user.has_perm(perm) for perm in perms)

    def _get_required_permissions(self, request, view, model_cls):
        """
        Returns the permissions that a user should have one of for a particular method.
        """
        action = get_model_action_for_view_action(request.method, view.action)

        format_kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name,
            'action': action
        }

        return [perm.format(**format_kwargs) for perm in self.permission_mapping[action]]


class InvestmentProjectAssociationChecker(ObjectAssociationCheckerBase):
    """
    Association check class for checking connection of user and
    InvestmentProject through the user's team.
    """

    restricted_actions = {'read', 'change'}

    def is_associated(self, request, view, obj):
        """Check for connection."""
        return any(request.user.dit_team_id == user.dit_team_id
                   for user in obj.get_associated_advisers())

    def should_apply_restrictions(self, request, view):
        """Check if restrictions should be applied."""
        action = get_model_action_for_view_action(request.method, view.action)
        if action not in self.restricted_actions:
            return False

        model = _get_model_for_view(view)

        format_kwargs = {
            'app_label': model._meta.app_label,
            'model_name': model._meta.model_name,
            'action': action
        }

        if request.user.has_perm(PermissionTemplates.all.format(**format_kwargs)):
            return False

        if request.user.has_perm(PermissionTemplates.associated.format(**format_kwargs)):
            return True

        raise RuntimeError('User does not have any relevant investment project permissions.')


class IsAssociatedToInvestmentProjectPermission(IsAssociatedToObjectPermission):
    """Permission based on InvestmentProjectAssociationChecker."""

    checker_class = InvestmentProjectAssociationChecker


class IsAssociatedToInvestmentProjectFilter(BaseFilterBackend):
    """Filter for LEPs users to see only associated InvestmentProjects"""

    actions_to_filter = {'list'}

    def __init__(self):
        """Initialise the instance."""
        self.checker = InvestmentProjectAssociationChecker()

    def filter_queryset(self, request, queryset, view):
        """Filters the queryset for restricted users."""
        view_should_be_filtered = view.action in self.actions_to_filter
        restrictions_are_active = self.checker.should_apply_restrictions(
            request=request, view=view
        )

        if view_should_be_filtered and restrictions_are_active:
            query = Q()
            for field in queryset.model.ASSOCIATED_ADVISER_TO_ONE_FIELDS:
                query |= Q(**{f'{field}__dit_team': request.user.dit_team})

            for field, subfield in queryset.model.ASSOCIATED_ADVISER_TO_MANY_FIELDS:
                query |= Q(**{f'{field}__{subfield}__dit_team': request.user.dit_team})
            return queryset.filter(query)
        return queryset


def _get_model_for_view(view):
    return getattr(view, 'model', None) or view.get_queryset().model
