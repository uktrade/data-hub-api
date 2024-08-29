import logging

from rest_framework import status
from rest_framework.response import Response

from config.settings.types import HawkScope
from datahub.core.auth import PaaSIPAuthentication
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

    authentication_classes = (PaaSIPAuthentication, HawkAuthentication)
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.data_flow_api

    def create(self, request):
        """POST route definition.

        This route needs to handle both creating new and updating existing instances
        because data is received automatically from a Data Flow pipeline.

        To reduce complexity of the pipeline, it was decided to have the separation
        logic within the API endpoint.
        """
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of leads.'},
                status.HTTP_400_BAD_REQUEST,
            )

        created_leads = []
        updated_leads = []
        errors = []

        for index, lead_data in enumerate(request.data):
            serializer = self.get_serializer(data=lead_data)
            if serializer.is_valid():
                _, created = self.perform_create(serializer)
                if created:
                    created_leads.append(serializer.validated_data)
                else:
                    updated_leads.append(serializer.validated_data)
            else:
                errors.append({'index': index, 'errors': serializer.errors})

        response_data = {}
        if created_leads:
            response_data['created'] = created_leads
        if updated_leads:
            response_data['updated'] = updated_leads
        if errors:
            response_data['errors'] = errors

        if not errors:
            # All leads have been created
            status_code = status.HTTP_201_CREATED
        elif len(errors) == len(request.data):
            # No leads have been created
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            # Some leads have been created, others failed
            status_code = status.HTTP_207_MULTI_STATUS
        logger.info(f'Processed {len(request.data)} EYB leads: {response_data}')
        return Response(response_data, status_code)

    def perform_create(self, serializer):
        """Processes a single lead.

        The `triage_hashed_uuid` and `user_hashed_uuid` field should be unique for each EYBLead
        instance. As a result, we use these to determine if a new instance is created, or an
        existing one updated.

        This overwrites the inherited BaseViewSet method.
        """
        validated_lead_data = serializer.validated_data
        lead_instance, created = EYBLead.objects.update_or_create(
            triage_hashed_uuid=validated_lead_data.get('triage_hashed_uuid'),
            user_hashed_uuid=validated_lead_data.get('user_hashed_uuid'),
            defaults=validated_lead_data,
        )
        return lead_instance, created
