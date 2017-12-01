from datahub.core.permissions import IsAssociatedToObjectPermission, ObjectAssociationCheckerBase


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
        method = self.get_method_for_view_action(view.action)
        return request.user.has_perm(self.base_permission_template.format(method=method))


class IsAssociatedToInvestmentProjectPermission(IsAssociatedToObjectPermission,
                                                InvestmentProjectAssociationChecker):
    """Permission based on InvestmentProjectAssociationChecker."""
