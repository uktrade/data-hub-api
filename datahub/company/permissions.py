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


class CompanyModelPermissions(ViewBasedModelPermissions):
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
