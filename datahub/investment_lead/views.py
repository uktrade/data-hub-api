import logging

from config.settings.types import HawkScope
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import SoftDeleteCoreViewSet
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import EYBLeadSerializer


logger = logging.getLogger(__name__)


class EYBLeadViewset(
    ArchivableViewSetMixin,
    SoftDeleteCoreViewSet,
    HawkResponseSigningMixin,
):
    serializer_class = EYBLeadSerializer
    queryset = EYBLead.objects.all()

    authentication_classes = (HawkAuthentication, )
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.data_flow_api
