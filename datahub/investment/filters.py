from django.db.models.query_utils import Q
from rest_framework.filters import BaseFilterBackend

from datahub.investment.permissions import InvestmentProjectAssociationChecker


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
