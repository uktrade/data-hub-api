from datahub.core.permissions import IsAssociatedToObjectPermission, ViewBasedModelPermissions
from datahub.core.utils import StrEnum
from datahub.investment.evidence.models import EvidenceDocument
from datahub.investment.models import InvestmentProject
from datahub.investment.permissions import (
    InvestmentProjectAssociationCheckerBase,
)


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated_investmentproject = '{app_label}.{action}_associated_{model_name}'


class _EvidenceDocumentViewToActionMapping:
    """Evidence Document view to action mapping class."""

    extra_view_to_action_mapping = {
        'download': 'view',
        'upload_complete_callback': 'change',
    }


class EvidenceDocumentModelPermissions(
    _EvidenceDocumentViewToActionMapping,
    ViewBasedModelPermissions
):
    """Evidence Document model permissions class."""

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
            _PermissionTemplate.all,
            _PermissionTemplate.associated_investmentproject,
        ),
    }


class InvestmentProjectEvidenceDocumentAssociationChecker(
    _EvidenceDocumentViewToActionMapping,
    InvestmentProjectAssociationCheckerBase,
):
    """
    Association checker for evidence documents, which checks association with the investment
    project linked to the evidence document.
    """

    restricted_actions = {'add', 'view', 'change', 'delete'}
    model = EvidenceDocument
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated_investmentproject


class IsAssociatedToInvestmentProjectEvidenceDocumentPermission(IsAssociatedToObjectPermission):
    """Permission class based on InvestmentProjectEvidenceDocumentAssociationChecker."""

    checker_class = InvestmentProjectEvidenceDocumentAssociationChecker

    def get_actual_object(self, obj):
        """Returns the investment project from an EvidenceDocument object."""
        return obj.investment_project

    def has_permission(self, request, view):
        """
        Returns whether the user has permissions for a view.

        Evidence documents view is attached to their parent investment project.
        If user has no permissions to view the investment project, access to the
        evidence documents endpoints should be blocked.
        """
        if self.checker.should_apply_restrictions(request, view.action):
            investment_project = InvestmentProject.objects.get(
                pk=request.parser_context['kwargs']['project_pk']
            )
            if not self.checker.is_associated(request, investment_project):
                return False

        return super().has_permission(request, view)
