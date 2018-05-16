from rest_framework.exceptions import ValidationError

from datahub.core.permissions import IsAssociatedToObjectPermission, ViewBasedModelPermissions
from datahub.core.utils import StrEnum
from datahub.investment.models import InvestmentProject
from datahub.investment.permissions import (
    InvestmentProjectAssociationCheckerBase, IsAssociatedToInvestmentProjectFilter
)
from datahub.investment.proposition.models import Proposition


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated_investmentproject = '{app_label}.{action}_associated_investmentproject_{model_name}'
    standard = '{app_label}.{action}_{model_name}'


class PropositionModelPermissions(ViewBasedModelPermissions):
    """Proposition model permissions class."""

    permission_mapping = {
        'read': (
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


class InvestmentProjectPropositionAssociationChecker(InvestmentProjectAssociationCheckerBase):
    """
    Association checker for propositions, which checks association with the investment
    project linked to the proposition.
    """

    restricted_actions = {'add', 'read', 'change'}
    model = Proposition
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated_investmentproject

    extra_view_to_action_mapping = {
        'complete': 'change',
        'abandon': 'change',
    }


class IsAssociatedToInvestmentProjectPropositionPermission(IsAssociatedToObjectPermission):
    """Permission class based on InvestmentProjectPropositionAssociationChecker."""

    checker_class = InvestmentProjectPropositionAssociationChecker

    def get_actual_object(self, obj):
        """Returns the investment project from an Proposition object."""
        return obj.investment_project


class IsAssociatedToInvestmentProjectPropositionFilter(IsAssociatedToInvestmentProjectFilter):
    """Filter class which enforces investment project proposition association permissions."""

    model_attribute = 'investment_project'
    checker_class = InvestmentProjectPropositionAssociationChecker


class HasAssociatedInvestmentProjectValidator:
    """Validator which enforces association permissions when adding or updating propositions."""

    required_message = 'This field is required.'
    non_associated_investment_project_message = (
        "You don't have permission to add a proposition for this investment project."
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

        checker = InvestmentProjectPropositionAssociationChecker()
        request = self.serializer.context['request']
        view = self.serializer.context['view']

        if not checker.should_apply_restrictions(request, view.action):
            return

        project_pk = request.parser_context['kwargs']['project_pk']
        investment_project = InvestmentProject.objects.get(pk=project_pk)

        if not checker.is_associated(request, investment_project):
            raise ValidationError({
                'investment_project': self.non_associated_investment_project_message,
            }, code='access_denied')

    def __repr__(self):
        """Returns the string representation of this object."""
        return f'{self.__class__.__name__}()'
