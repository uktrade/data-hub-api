from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import BasePermission

from datahub.core.permissions import (
    get_model_action_for_view_action, IsAssociatedToObjectPermission, ViewBasedModelPermissions
)
from datahub.core.utils import StrEnum
from datahub.interaction.models import Interaction
from datahub.investment.permissions import (
    InvestmentProjectAssociationCheckerBase, IsAssociatedToInvestmentProjectFilter
)


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated_investmentproject = '{app_label}.{action}_associated_investmentproject_{model_name}'
    policy_feedback = '{app_label}.{action}_policy_feedback_{model_name}'
    standard = '{app_label}.{action}_{model_name}'


# Mapping from kind to permission required to add/edit/view interactions with that kind
# (None means no additional permission required over standard interaction permissions.)
_KIND_PERMISSION_MAPPING = {
    Interaction.KINDS.interaction: None,
    Interaction.KINDS.service_delivery: None,
    Interaction.KINDS.policy_feedback: _PermissionTemplate.policy_feedback
}


class InteractionModelPermissions(ViewBasedModelPermissions):
    """Interaction model permissions class."""

    permission_mapping = {
        'view': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated_investmentproject,
        ),
        'add': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated_investmentproject,
        ),
        'change': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated_investmentproject,
        ),
        'delete': (
            _PermissionTemplate.standard,
        ),
    }


class InvestmentProjectInteractionAssociationChecker(InvestmentProjectAssociationCheckerBase):
    """
    Association checker for interactions, which checks association with the investment
    project linked to the interaction.
    """

    restricted_actions = {'add', 'view', 'change'}
    model = Interaction
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated_investmentproject


class IsAssociatedToInvestmentProjectInteractionPermission(IsAssociatedToObjectPermission):
    """Permission class based on InvestmentProjectInteractionAssociationChecker."""

    checker_class = InvestmentProjectInteractionAssociationChecker

    def get_actual_object(self, obj):
        """Returns the investment project from an Interaction object."""
        return obj.investment_project


class IsAssociatedToInvestmentProjectInteractionFilter(IsAssociatedToInvestmentProjectFilter):
    """Filter class which enforces investment project interaction association permissions."""

    model_attribute = 'investment_project'
    checker_class = InvestmentProjectInteractionAssociationChecker


class HasAssociatedInvestmentProjectValidator:
    """Validator which enforces association permissions when adding interactions."""

    required_message = 'This field is required.'
    non_associated_investment_project_message = (
        "You don't have permission to add an interaction for this investment project."
    )

    def __init__(self):
        """
        Initialises the validator.
        """
        self.serializer = None

    def set_context(self, serializer):
        """
        Saves a reference to the serializer object.

        Called by DRF.
        """
        self.serializer = serializer

    def __call__(self, attrs):
        """
        Performs validation. Called by DRF.

        :param attrs:   Serializer data (post-field-validation/processing)
        """
        if self.serializer.instance:
            return

        checker = InvestmentProjectInteractionAssociationChecker()
        request = self.serializer.context['request']
        view = self.serializer.context['view']

        if not checker.should_apply_restrictions(request, view.action):
            return

        investment_project = attrs.get('investment_project')

        if investment_project is None:
            raise ValidationError({
                'investment_project': self.required_message
            }, code='null')

        if not checker.is_associated(request, investment_project):
            raise ValidationError({
                'investment_project': self.non_associated_investment_project_message
            }, code='access_denied')

    def __repr__(self):
        """Returns the string representation of this object."""
        return f'{self.__class__.__name__}()'


class PolicyFeedbackObjectPermission(BasePermission):
    """DRF permission class to enforce interaction kind permissions."""

    def has_object_permission(self, request, view, obj):
        """Checks if the user has permission to access a specific object."""
        return obj.kind in get_allowed_kinds(request, view.action)


class PolicyFeedbackPermissionFilter(BaseFilterBackend):
    """Filter to enforce interaction kind permissions."""

    actions_to_filter = {'list'}

    def filter_queryset(self, request, queryset, view):
        """Filters the queryset for restricted users."""
        if view.action not in self.actions_to_filter:
            return queryset

        allowed_kinds = get_allowed_kinds(request, view.action)
        return queryset.filter(kind__in=allowed_kinds)


class KindPermissionValidator:
    """Class-level validator to enforce kind permissions when adding interactions."""

    access_denied_message = 'You don’t have permission to add this type of interaction.'

    def __init__(self):
        """Initialises the validator."""
        self.serializer = None

    def set_context(self, serializer):
        """
        Saves a reference to the serializer object.

        Called by DRF.
        """
        self.serializer = serializer

    def __call__(self, attrs):
        """
        Performs validation. Called by DRF.

        :param attrs:   Serializer data (post-field-validation/processing)
        """
        if self.serializer.instance:
            return

        request = self.serializer.context['request']
        view = self.serializer.context['view']

        allowed_kinds = get_allowed_kinds(request, view.action)

        if attrs['kind'] not in allowed_kinds:
            raise ValidationError({
                'kind': self.access_denied_message
            }, code='access_denied')

    def __repr__(self):
        """Returns the string representation of this object."""
        return f'{self.__class__.__name__}()'


def get_allowed_kinds(request, view_action):
    """
    Gets the kinds the user is allowed to access and manage.

    Used to enforce policy feedback permissions.
    """
    return [kind for kind, _ in Interaction.KINDS if _is_kind_allowed(kind, request, view_action)]


def _is_kind_allowed(kind, request, view_action):
    permission_template = _KIND_PERMISSION_MAPPING[kind]
    if permission_template is None:
        return True

    action = get_model_action_for_view_action(request.method, view_action)

    format_kwargs = {
        'app_label': Interaction._meta.app_label,
        'model_name': Interaction._meta.model_name,
        'action': action
    }

    permission = permission_template.format(**format_kwargs)

    return request.user.has_perm(permission)
