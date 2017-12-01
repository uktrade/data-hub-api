from django.db.models.query_utils import Q
from rest_framework.filters import BaseFilterBackend

from datahub.core.permissions import (
    get_method_for_view_action, IsAssociatedToObjectPermission, ObjectAssociationCheckerBase
)


class InvestmentProjectAssociationChecker(ObjectAssociationCheckerBase):
    """
    Association check class for checking connection of user and
    InvestmentProject through the user's team.
    """

    base_permission_template = 'investment.{method}_associated_investmentproject'

    def is_associated(self, request, view, obj):
        """Check for connection."""
        return any(request.user.dit_team_id == user.dit_team_id
                   for user in obj.get_associated_advisers())

    def should_apply_restrictions(self, request, view):
        """Check if restrictions should be applied."""
        method = get_method_for_view_action(view.action)
        return request.user.has_perm(self.base_permission_template.format(method=method))


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
