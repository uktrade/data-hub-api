from datahub.core.permissions import IsAssociatedToObjectPermission, ViewBasedModelPermissions
from datahub.core.utils import StrEnum
from datahub.investment.permissions import (
    HasAssociatedInvestmentProjectValidator,
    InvestmentProjectAssociationCheckerBase,
    IsAssociatedToInvestmentProjectFilter
)
from datahub.investment.proposition.models import Proposition, PropositionDocument


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated_investmentproject = '{app_label}.{action}_associated_investmentproject_{model_name}'
    standard = '{app_label}.{action}_{model_name}'


class _PropositionViewToActionMapping:
    """Proposition view to action mapping class."""

    extra_view_to_action_mapping = {
        'complete': 'change',
        'abandon': 'change',
    }


class PropositionModelPermissions(_PropositionViewToActionMapping, ViewBasedModelPermissions):
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


class InvestmentProjectPropositionAssociationChecker(
    _PropositionViewToActionMapping,
    InvestmentProjectAssociationCheckerBase,
):
    """
    Association checker for propositions, which checks association with the investment
    project linked to the proposition.
    """

    restricted_actions = {'add', 'read', 'change'}
    model = Proposition
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated_investmentproject


class IsAssociatedToInvestmentProjectPropositionPermission(IsAssociatedToObjectPermission):
    """Permission class based on InvestmentProjectPropositionAssociationChecker."""

    checker_class = InvestmentProjectPropositionAssociationChecker

    def get_actual_object(self, obj):
        """Returns the investment project from an Proposition object."""
        return obj.investment_project


class IsAssociatedToInvestmentProjectPropositionFilter(IsAssociatedToInvestmentProjectFilter):
    """Filter class which enforces investment project proposition association permission."""

    model_attribute = 'investment_project'
    checker_class = InvestmentProjectPropositionAssociationChecker


class PropositionHasAssociatedInvestmentProjectValidator(HasAssociatedInvestmentProjectValidator):
    """Validator which enforces association permissions when adding or updating propositions."""

    non_associated_investment_project_message = (
        "You don't have permission to add a proposition for this investment project."
    )
    checker = InvestmentProjectPropositionAssociationChecker()


class _PropositionDocumentViewToActionMapping:
    """Proposition Document view to action mapping class."""

    extra_view_to_action_mapping = {
        'download': 'read',
        'upload_complete_callback': 'change',
    }


class PropositionDocumentModelPermissions(
    _PropositionDocumentViewToActionMapping,
    ViewBasedModelPermissions
):
    """Proposition Document model permissions class."""

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
            _PermissionTemplate.associated_investmentproject,
        ),
    }


class InvestmentProjectPropositionDocumentAssociationChecker(
    _PropositionDocumentViewToActionMapping,
    InvestmentProjectAssociationCheckerBase,
):
    """
    Association checker for propositions, which checks association with the investment
    project linked to the proposition.
    """

    restricted_actions = {'add', 'read', 'change'}
    model = PropositionDocument
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated_investmentproject


class IsAssociatedToInvestmentProjectPropositionDocumentPermission(IsAssociatedToObjectPermission):
    """Permission class based on InvestmentProjectPropositionAssociationChecker."""

    checker_class = InvestmentProjectPropositionDocumentAssociationChecker

    def get_actual_object(self, obj):
        """Returns the investment project from an Proposition object."""
        return obj.proposition.investment_project


class IsAssociatedToInvestmentProjectPropositionDocumentFilter(
    IsAssociatedToInvestmentProjectFilter
):
    """
    Filter class which enforces investment project proposition document association permission.
    """

    model_attribute = 'investment_project'
    checker_class = InvestmentProjectPropositionDocumentAssociationChecker


class PropositionDocumentHasAssociatedInvestmentProjectValidator(
    HasAssociatedInvestmentProjectValidator
):
    """Validator which enforces association permissions when adding or updating propositions."""

    required_message = 'This field is required.'
    non_associated_investment_project_message = (
        "You don't have permission to add a proposition document for this investment project."
    )
