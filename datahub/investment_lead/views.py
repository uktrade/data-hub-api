import logging

from rest_framework import serializers, status
from rest_framework.response import Response

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

    def create(self, request):
        eyb_lead_serializer = self.serializer_class(data=request.data)
        try:
            eyb_lead_serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            message = 'EYB data failed DH serializer validation'
            extra_data = {
                'eyb_lead_serializer_errors': eyb_lead_serializer.errors,
            }
            logger.error(message, extra=extra_data)
            raise

        # Create or update to prevent duplicates
        eyb_lead_data = eyb_lead_serializer.validated_data
        eyb_lead, created = EYBLead.objects.update_or_create(
            triage_hashed_uuid=eyb_lead_data.get('triage_hashed_uuid'),
            user_hashed_uuid=eyb_lead_data.get('user_hashed_uuid'),
            defaults=eyb_lead_data)

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(
            eyb_lead_serializer.to_representation(eyb_lead),
            status=status_code,
        )
