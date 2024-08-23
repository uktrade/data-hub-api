import logging

from rest_framework.permissions import IsAuthenticated

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import SoftDeleteCoreViewSet
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import EYBLeadSerializer

logger = logging.getLogger(__name__)


class EYBLeadViewset(ArchivableViewSetMixin, SoftDeleteCoreViewSet):
    serializer_class = EYBLeadSerializer
    queryset = EYBLead.objects.all()

    permission_classes = (IsAuthenticated,)
