from rest_framework.exceptions import ValidationError

from datahub.core.permissions import IsAssociatedToObjectPermission, ViewBasedModelPermissions
from datahub.core.utils import StrEnum
from datahub.interaction.models import Interaction
from datahub.investment.permissions import (
    InvestmentProjectAssociationCheckerBase, IsAssociatedToInvestmentProjectFilter
)


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    associated_investmentproject = '{app_label}.{action}_associated_investmentproject_{model_name}'
    standard = '{app_label}.{action}_{model_name}'


class InteractionModelPermissions(ViewBasedModelPermissions):
    """Interaction model permissions class."""

    permission_mapping = {
        'read': (
            _PermissionTemplate.standard,
            _PermissionTemplate.associated_investmentproject,
        ),
        'add': (
            _PermissionTemplate.standard,
            _PermissionTemplate.associated_investmentproject,
        ),
        'change': (
            _PermissionTemplate.standard,
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

    restricted_actions = {'add', 'read', 'change'}
    model = Interaction
    all_permission_template = _PermissionTemplate.standard
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
