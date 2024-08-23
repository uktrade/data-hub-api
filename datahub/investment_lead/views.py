import logging

from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import EYBLeadSerializer
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import SoftDeleteCoreViewSet

logger = logging.getLogger(__name__)


class EYBLeadViewset(ArchivableViewSetMixin, SoftDeleteCoreViewSet):
    serializer_class = EYBLeadSerializer
    queryset = EYBLead.objects.all()

    permission_classes = (IsAuthenticated,)
