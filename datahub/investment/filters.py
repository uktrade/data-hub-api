from rest_framework.filters import BaseFilterBackend

from datahub.investment.permissions import UserTeamInvestmentProjectAssociationCheck


class IsTeamAssociatedToInvestmentProjectFilter(BaseFilterBackend,
                                                UserTeamInvestmentProjectAssociationCheck):
    """Filter for LEPs users to see only associated InvestmentProjects"""

    def filter_queryset(self, request, queryset, view):
        """Filtering the queryset for LEPs users for InvestmentProjects"""
        if self.check_condition(request=request, view=view):
            return queryset.filter(team_members__adviser__dit_team=request.user.dit_team)
        return queryset
