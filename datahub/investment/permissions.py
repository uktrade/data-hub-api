from django.core.exceptions import ImproperlyConfigured

from datahub.core.permissions import IsAssociatedToObjectPermission, UserObjectAssociationCheck
from datahub.investment.models import InvestmentProject


class UserTeamInvestmentProjectAssociationCheck(UserObjectAssociationCheck):
    """
    Association check class for checking connection of user and
    InvestmentProject through the user's team.
    """

    base_permission_template = 'investment.{method}_associated_investmentproject'

    def is_associated(self, request, view, obj):
        """Check for connection."""
        if not isinstance(obj, InvestmentProject):
            raise ImproperlyConfigured(f'{self} needs to be used on InvestmentProject view')
        return any(request.user.dit_team_id == user.dit_team_id
                   for user in obj.get_associated_advisors())

    def check_condition(self, request, view):
        """Check if condition should be applied."""
        method = self.action_to_method(view.action)
        return request.user.has_perm(self.base_permission_template.format(method=method))


class IsTeamAssociatedToInvestmentProjectPermission(IsAssociatedToObjectPermission,
                                                    UserTeamInvestmentProjectAssociationCheck):
    """Permission based on UserTeamInvestmentProjectAssociationCheck."""

    pass
