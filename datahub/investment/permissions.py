from datahub.search import elasticsearch
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
        return obj.team_members.filter(adviser__dit_team=request.user.dit_team).count() > 0

    def check_condition(self, request, view):
        """Check if condition should be applied."""
        try:
            action = view.action
        except AttributeError:
            action = 'list'

        method = self.action_2_method(action=action)
        return request.user.has_perm(self.base_permission_template.format(method=method))

    def get_filtering_data(self, validated_data):
        filters, ranges = super().get_filtering_data(validated_data=validated_data)
        if self.check_condition(self.request, self):

            dit_team_id = self.request.user.dit_team.id if \
                self.request.user and \
                self.request.user.dit_team and \
                self.request.user.dit_team.id else None

            filters.update({'team_members.dit_team.id': str(dit_team_id)})
        return elasticsearch.date_range_fields(filters)


class IsTeamAssociatedToInvestmentProjectPermission(IsAssociatedToObjectPermission,
                                                    UserTeamInvestmentProjectAssociationCheck):
    """Permission based on UserTeamInvestmentProjectAssociationCheck."""

    pass
