from datahub.core.permissions import IsAssociatedToObjectPermission, ViewBasedModelPermissions
from datahub.core.utils import StrEnum
from datahub.investment.evidence.models import EvidenceGroup
from datahub.investment.permissions import (
    HasAssociatedInvestmentProjectValidator,
    InvestmentProjectAssociationCheckerBase,
    IsAssociatedToInvestmentProjectFilter,
)


class _PermissionTemplate(StrEnum):
    """Permission codename templates."""

    all = '{app_label}.{action}_all_{model_name}'
    associated_investmentproject = '{app_label}.{action}_associated_{model_name}'
    standard = '{app_label}.{action}_{model_name}'


class EvidenceGroupModelPermissions(ViewBasedModelPermissions):
    """Evidence Group model permissions class."""

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


class InvestmentProjectEvidenceGroupAssociationChecker(
    InvestmentProjectAssociationCheckerBase,
):
    """
    Association checker for evidence groups, which checks association with the investment
    project linked to the evidence group.
    """

    restricted_actions = {'add', 'read', 'change'}
    model = EvidenceGroup
    all_permission_template = _PermissionTemplate.all
    associated_permission_template = _PermissionTemplate.associated_investmentproject


class IsAssociatedToInvestmentProjectEvidenceGroupPermission(IsAssociatedToObjectPermission):
    """Permission class based on InvestmentProjectPropositionAssociationChecker."""

    checker_class = InvestmentProjectEvidenceGroupAssociationChecker

    def get_actual_object(self, obj):
        """Returns the investment project from an EvidenceGroup object."""
        return obj.investment_project


class IsAssociatedToInvestmentProjectEvidenceGroupFilter(IsAssociatedToInvestmentProjectFilter):
    """Filter class which enforces investment project evidence group association permission."""

    model_attribute = 'investment_project'
    checker_class = InvestmentProjectEvidenceGroupAssociationChecker


class EvidenceGroupHasAssociatedInvestmentProjectValidator(
    HasAssociatedInvestmentProjectValidator
):
    """Validator which enforces association permissions when adding or updating evidence groups."""

    non_associated_investment_project_message = (
        "You don't have permission to add an evidence group for this investment project."
    )
    checker = InvestmentProjectEvidenceGroupAssociationChecker()
