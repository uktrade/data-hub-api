from datahub.core.permissions import IsAssociatedToObjectPermission, ViewBasedModelPermissions
from datahub.core.utils import StrEnum
from datahub.investment.permissions import (
    InvestmentProjectAssociationCheckerBase,
    IsAssociatedToInvestmentProjectPermissionMixin,
)
from datahub.investment.proposition.models import Proposition, PropositionDocument


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated = '{app_label}.{action}_associated_{model_name}'
    not_allowed = '{app_label}.{action}_not_allowed_{model_name}'


class _PropositionViewToActionMapping:
    """Proposition view to action mapping class."""

    extra_view_to_action_mapping = {
        'complete': 'change',
        'abandon': 'change',
    }


class PropositionModelPermissions(_PropositionViewToActionMapping, ViewBasedModelPermissions):
    """Proposition model permissions class."""

    permission_mapping = {
        'view': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'add': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'change': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'delete': (
            # user is not allowed to delete a proposition. Proposition can only be abandoned.
            _PermissionTemplate.not_allowed,
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

    restricted_actions = {'add', 'view', 'change'}
    model = Proposition
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated


class IsAssociatedToInvestmentProjectPropositionPermission(
    IsAssociatedToInvestmentProjectPermissionMixin,
    IsAssociatedToObjectPermission,
):
    """Permission class based on InvestmentProjectPropositionAssociationChecker."""

    checker_class = InvestmentProjectPropositionAssociationChecker

    def get_actual_object(self, obj):
        """Returns the investment project from an Proposition object."""
        return obj.investment_project


class _PropositionDocumentViewToActionMapping:
    """Proposition Document view to action mapping class."""

    extra_view_to_action_mapping = {
        'download': 'view',
        'upload_complete_callback': 'change',
    }


class PropositionDocumentModelPermissions(
    _PropositionDocumentViewToActionMapping,
    ViewBasedModelPermissions,
):
    """Proposition Document model permissions class."""

    permission_mapping = {
        'view': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'add': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'change': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
        ),
        'delete': (
            _PermissionTemplate.all,
            _PermissionTemplate.associated,
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

    restricted_actions = {'add', 'view', 'change', 'delete'}
    model = PropositionDocument
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated


class IsAssociatedToInvestmentProjectPropositionDocumentPermission(
    IsAssociatedToInvestmentProjectPermissionMixin,
    IsAssociatedToObjectPermission,
):
    """Permission class based on InvestmentProjectPropositionAssociationChecker."""

    checker_class = InvestmentProjectPropositionDocumentAssociationChecker

    def get_actual_object(self, obj):
        """Returns the investment project from an Proposition object."""
        return obj.proposition.investment_project
