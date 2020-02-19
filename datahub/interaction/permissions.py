from rest_framework.exceptions import ValidationError

from datahub.core.permissions import (
    IsAssociatedToObjectPermission,
    ViewBasedModelPermissions,
)
from datahub.core.utils import StrEnum
from datahub.interaction.models import Interaction
from datahub.investment.project.permissions import (
    InvestmentProjectAssociationCheckerBase,
    IsAssociatedToInvestmentProjectFilter,
)


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated_investmentproject = '{app_label}.{action}_associated_investmentproject_{model_name}'
    standard = '{app_label}.{action}_{model_name}'


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

    requires_context = True
    required_message = 'This field is required.'
    non_associated_investment_project_message = (
        "You don't have permission to add an interaction for this investment project."
    )

    def __call__(self, attrs, serializer):
        """
        Performs validation. Called by DRF.

        :param attrs:   Serializer data (post-field-validation/processing)
        """
        # If the validator is being called from e.g. the admin site import interactions tool
        # do nothing, as the logic below is only really relevant for standard users directly
        # creating or editing interactions
        if not serializer.context.get('check_association_permissions', True):
            return

        if serializer.instance:
            return

        checker = InvestmentProjectInteractionAssociationChecker()
        request = serializer.context['request']
        view = serializer.context['view']

        if not checker.should_apply_restrictions(request, view.action):
            return

        investment_project = attrs.get('investment_project')

        if investment_project is None:
            raise ValidationError(
                {
                    'investment_project': self.required_message,
                },
                code='null',
            )

        if not checker.is_associated(request, investment_project):
            raise ValidationError(
                {
                    'investment_project': self.non_associated_investment_project_message,
                },
                code='access_denied',
            )

    def __repr__(self):
        """Returns the string representation of this object."""
        return f'{self.__class__.__name__}()'
