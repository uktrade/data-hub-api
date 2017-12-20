from django.db.models.query_utils import Q
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import BasePermission

from datahub.core.permissions import (
    get_model_action_for_view_action,
    IsAssociatedToObjectPermission,
    ObjectAssociationCheckerBase
)
from datahub.core.utils import StrEnum
from datahub.investment.models import InvestmentProject


class _PermissionTemplate(StrEnum):
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

    many_to_many = False

    permission_mapping = {
        'add': (
            _PermissionTemplate.standard,
        ),
        'read': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'change': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'delete': (
            _PermissionTemplate.standard,
        ),
    }

    def has_permission(self, request, view):
        """Returns whether the user has permission for a view."""
        if not request.user or not request.user.is_authenticated:
            return False

        perms = self._get_required_permissions(request, view, InvestmentProject)

        return any(request.user.has_perm(perm) for perm in perms)

    def _get_required_permissions(self, request, view, model_cls):
        """
        Returns the permissions that a user should have one of for a particular method.
        """
        action = get_model_action_for_view_action(
            request.method, view.action, many_to_many=self.many_to_many
        )

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

    many_to_many = False
    restricted_actions = {'read', 'change'}

    def is_associated(self, request, obj):
        """Check for connection."""
        if self.should_exclude_all(request):
            return False

        return any(request.user.dit_team_id == user.dit_team_id
                   for user in obj.get_associated_advisers())

    def should_apply_restrictions(self, request, view_action, model):
        """Check if restrictions should be applied."""
        action = get_model_action_for_view_action(
            request.method, view_action, many_to_many=self.many_to_many
        )
        if action not in self.restricted_actions:
            return False

        format_kwargs = {
            'app_label': model._meta.app_label,
            'model_name': model._meta.model_name,
            'action': action
        }

        if request.user.has_perm(_PermissionTemplate.all.format(**format_kwargs)):
            return False

        if request.user.has_perm(_PermissionTemplate.associated.format(**format_kwargs)):
            return True

        raise RuntimeError('User does not have any relevant investment project permissions.')

    @staticmethod
    def should_exclude_all(request):
        """Get whether all results should be filtered out (when restrictions are active)."""
        return not (request.user and request.user.dit_team_id)


class IsAssociatedToInvestmentProjectPermission(IsAssociatedToObjectPermission):
    """Permission based on InvestmentProjectAssociationChecker."""

    checker_class = InvestmentProjectAssociationChecker


class IsAssociatedToInvestmentProjectFilter(BaseFilterBackend):
    """Filter for LEPs users to see only associated InvestmentProjects."""

    actions_to_filter = {'list'}

    def __init__(self):
        """Initialise the instance."""
        self.checker = InvestmentProjectAssociationChecker()

    def filter_queryset(self, request, queryset, view):
        """Filters the queryset for restricted users."""
        view_should_be_filtered = view.action in self.actions_to_filter
        restrictions_are_active = self.checker.should_apply_restrictions(
            request, view.action, queryset.model
        )

        if not (view_should_be_filtered and restrictions_are_active):
            return queryset

        if self.checker.should_exclude_all(request):
            return queryset.none()

        to_one_filters, to_many_filters = get_association_filters(request.user.dit_team_id)

        query = Q()
        for field, value in to_one_filters:
            query |= Q(**{f'{field}__dit_team_id': value})

        for field, value in to_many_filters:
            full_field_name = f'{field.field_name}__{field.subfield_name}__dit_team_id'
            query |= Q(**{full_field_name: value})
        return queryset.filter(query)


class InvestmentProjectTeamMemberModelPermissions(InvestmentProjectModelPermissions):
    """
    Custom permissions class for team member views.

    Uses InvestmentProject model permissions.
    """

    many_to_many = True


class InvestmentProjectTeamMemberAssociationChecker(InvestmentProjectAssociationChecker):
    """
    Association checker for checking association of a user with an investment project,
    via a team member object.
    """

    many_to_many = True
    restricted_actions = {'read', 'change'}


class IsAssociatedToInvestmentProjectTeamMemberPermission(IsAssociatedToObjectPermission):
    """Permission based on InvestmentProjectTeamMemberAssociationChecker."""

    checker_class = InvestmentProjectTeamMemberAssociationChecker

    def has_permission(self, request, view):
        """Checks if the user has permission using the investment project object."""
        return self._check_actual_object_permission(request, view, view.get_project())

    def get_actual_object(self, obj):
        """Returns the investment project from an InvestmentProjectTeamMember object."""
        return obj.investment_project


def get_association_filters(dit_team_id):
    """
    Gets a list of rules that can be used to restrict a query set to associated projects.

    Two lists of rules are returned – one for to-one fields, one for to-many fields.

    The rules are a list of field name and value pairs. Objects must match one of these rules
    to be considered an associated project.
    """
    if dit_team_id is None:
        raise ValueError('dit_team_id cannot be None.')

    to_one_fields, to_many_fields = InvestmentProject.get_association_fields()

    to_one_filters = [(field, dit_team_id) for field in to_one_fields]
    to_many_filters = [(field, dit_team_id) for field in to_many_fields]

    return to_one_filters, to_many_filters
