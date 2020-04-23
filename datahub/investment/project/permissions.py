from django.db.models.query_utils import Q
from rest_framework.filters import BaseFilterBackend

from datahub.core.permissions import (
    get_model_action_for_view_action,
    IsAssociatedToObjectPermission,
    ObjectAssociationCheckerBase,
    ViewBasedModelPermissions,
)
from datahub.core.utils import StrEnum
from datahub.investment.project.models import InvestmentProject


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated = '{app_label}.{action}_associated_{model_name}'
    standard = '{app_label}.{action}_{model_name}'
    stage_to_won = '{app_label}.{action}_stage_to_won_{model_name}'


class InvestmentProjectModelPermissions(ViewBasedModelPermissions):
    """
    Custom permissions class for investment views.

    This differs from the standard DjangoModelPermissions class in that:
    - the permissions mapping is based on view/model actions rather than HTTP methods
    - the user only needs to have one the permissions corresponding to each action, rather than
      all of them
    """

    many_to_many = False
    model = InvestmentProject

    permission_mapping = {
        'add': (
            _PermissionTemplate.standard,
        ),
        'view': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'change': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
            _PermissionTemplate.stage_to_won,
        ),
        'delete': (
            _PermissionTemplate.standard,
        ),
    }


class InvestmentProjectAssociationCheckerBase(ObjectAssociationCheckerBase):
    """
    Base class for investment project association checkers.
    """

    many_to_many = False
    restricted_actions = None
    model = None
    all_permission_template = None
    associated_permission_template = None

    extra_view_to_action_mapping = None

    def is_associated(self, request, obj):
        """Check for connection."""
        if self.should_exclude_all(request):
            return False

        return any(request.user.dit_team_id == user.dit_team_id
                   for user in obj.get_associated_advisers())

    def should_apply_restrictions(self, request, view_action):
        """Check if restrictions should be applied."""
        action = get_model_action_for_view_action(
            request.method,
            view_action,
            many_to_many=self.many_to_many,
            extra_view_to_action_mapping=self.extra_view_to_action_mapping,
        )
        if action not in self.restricted_actions:
            return False

        format_kwargs = {
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
            'action': action,
        }

        if request.user.has_perm(self.all_permission_template.format(**format_kwargs)):
            return False

        if request.user.has_perm(self.associated_permission_template.format(**format_kwargs)):
            return True

        raise RuntimeError('User does not have any relevant investment project permissions.')

    @staticmethod
    def should_exclude_all(request):
        """Get whether all results should be filtered out (when restrictions are active)."""
        return not (request.user and request.user.dit_team_id)


class InvestmentProjectAssociationChecker(InvestmentProjectAssociationCheckerBase):
    """
    Association check class for checking connection of user and
    InvestmentProject through the user's team.
    """

    many_to_many = False
    restricted_actions = {'view', 'change'}
    model = InvestmentProject
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated


class IsAssociatedToInvestmentProjectPermission(IsAssociatedToObjectPermission):
    """Permission based on InvestmentProjectAssociationChecker."""

    checker_class = InvestmentProjectAssociationChecker


class IsAssociatedToInvestmentProjectPermissionMixin:
    """
    This checks if user has permission to access a view attached to Investment Project.

    It is meant to be used with IsAssociatedToObjectPermission.
    """

    def has_permission(self, request, view):
        """Returns whether the user has permissions for a view."""
        if self.checker.should_apply_restrictions(request, view.action):
            investment_project = InvestmentProject.objects.get(
                pk=request.parser_context['kwargs']['project_pk'],
            )
            if not self.checker.is_associated(request, investment_project):
                return False

        return super().has_permission(request, view)


class IsAssociatedToInvestmentProjectFilter(BaseFilterBackend):
    """Filter for LEPs users to see only associated InvestmentProjects."""

    actions_to_filter = {'list'}
    model_attribute = None
    checker_class = InvestmentProjectAssociationChecker

    def __init__(self):
        """Initialise the instance."""
        self.checker = self.checker_class()

    def filter_queryset(self, request, queryset, view):
        """Filters the queryset for restricted users."""
        view_should_be_filtered = view.action in self.actions_to_filter
        restrictions_are_active = self.checker.should_apply_restrictions(request, view.action)

        if not (view_should_be_filtered and restrictions_are_active):
            return queryset

        if self.checker.should_exclude_all(request):
            return queryset.none()

        to_one_filters, to_many_filters = get_association_filters(request.user.dit_team_id)
        field_prefix = self._get_filter_field_prefix()

        query = Q()
        for field, value in to_one_filters:
            full_field_name = f'{field_prefix}{field}__dit_team_id'
            query |= Q(**{full_field_name: value})

        for field, value in to_many_filters:
            full_field_name = (f'{field_prefix}{field.field_name}__'
                               f'{field.subfield_name}__dit_team_id')
            query |= Q(**{full_field_name: value})
        return queryset.filter(query).distinct()

    def _get_filter_field_prefix(self):
        return f'{self.model_attribute}__' if self.model_attribute else ''


class InvestmentProjectTeamMemberModelPermissions(InvestmentProjectModelPermissions):
    """
    Custom permissions class for team member views.

    Uses InvestmentProject model permissions.
    """

    many_to_many = True


class InvestmentProjectTeamMemberAssociationChecker(InvestmentProjectAssociationCheckerBase):
    """
    Association checker for checking association of a user with an investment project,
    via a team member object.
    """

    many_to_many = True
    restricted_actions = {'view', 'change'}
    model = InvestmentProject
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated


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
