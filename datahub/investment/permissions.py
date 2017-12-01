from django.db.models.query_utils import Q
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import BasePermission

from datahub.core.permissions import (
    get_method_for_view_action, IsAssociatedToObjectPermission, ObjectAssociationCheckerBase
)


class InvestmentProjectModelPermissions(BasePermission):
    """
    Custom permissions class for investment views.

    This differs from the standard DjangoModelPermissions class in that users are required to have
    any one of the permissions in the values of perms_map, rather than all of the permissions in
    each value.
    """

    perms_map = {
        'GET': (
            '{app_label}.read_{model_name}',
            '{app_label}.read_associated_{model_name}'
        ),
        'OPTIONS': (),
        'HEAD': (),
        'POST': (
            '{app_label}.add_{model_name}',
        ),
        'PUT': (
            '{app_label}.change_{model_name}',
            '{app_label}.change_associated_{model_name}'
        ),
        'PATCH': (
            '{app_label}.change_{model_name}',
            '{app_label}.change_associated_{model_name}'
        ),
        'DELETE': (
            '{app_label}.delete_{model_name}',
        ),
    }

    def get_required_permissions(self, method, model_cls):
        """
        Returns the permissions that a user should have one of for a particular method.
        """
        format_kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }

        if method not in self.perms_map:
            raise MethodNotAllowed(method)

        return [perm.format(**format_kwargs) for perm in self.perms_map[method]]

    def has_permission(self, request, view):
        """Returns whether the user has permission for a view."""
        if not request.user or not request.user.is_authenticated:
            return False

        model = view.get_queryset().model
        perms = self.get_required_permissions(request.method, model)

        return any(request.user.has_perm(perm) for perm in perms)


class InvestmentProjectAssociationChecker(ObjectAssociationCheckerBase):
    """
    Association check class for checking connection of user and
    InvestmentProject through the user's team.
    """

    restricted_methods = {'read', 'change'}
    associated_permission_template = 'investment.{method}_associated_investmentproject'
    all_permission_template = 'investment.{method}_investmentproject'

    def is_associated(self, request, view, obj):
        """Check for connection."""
        return any(request.user.dit_team_id == user.dit_team_id
                   for user in obj.get_associated_advisers())

    def should_apply_restrictions(self, request, view):
        """Check if restrictions should be applied."""
        method = get_method_for_view_action(view.action)
        if method not in self.restricted_methods:
            return False

        if request.user.has_perm(self.all_permission_template.format(method=method)):
            return False

        return request.user.has_perm(self.associated_permission_template.format(method=method))


class IsAssociatedToInvestmentProjectPermission(IsAssociatedToObjectPermission,
                                                InvestmentProjectAssociationChecker):
    """Permission based on InvestmentProjectAssociationChecker."""


class IsAssociatedToInvestmentProjectFilter(BaseFilterBackend,
                                            InvestmentProjectAssociationChecker):
    """Filter for LEPs users to see only associated InvestmentProjects"""

    actions_to_filter = {'list'}

    def filter_queryset(self, request, queryset, view):
        """Filtering the queryset for LEPs users for InvestmentProjects"""
        view_should_be_filtered = view.action in self.actions_to_filter
        restrictions_are_active = self.should_apply_restrictions(request=request, view=view)

        if view_should_be_filtered and restrictions_are_active:
            return queryset.filter(
                Q(team_members__adviser__dit_team=request.user.dit_team)
                | Q(created_by__dit_team=request.user.dit_team)
            )
        return queryset
