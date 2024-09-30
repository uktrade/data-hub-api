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
from datahub.core.viewsets import SoftDeleteCoreViewSet
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import (
    CreateEYBLeadSerializer,
    RetrieveEYBLeadSerializer,
)
from datahub.metadata.models import Sector


logger = logging.getLogger(__name__)


class EYBLeadViewSet(HawkResponseSigningMixin, SoftDeleteCoreViewSet):
    queryset = EYBLead.objects.filter(archived=False)
    required_hawk_scope = HawkScope.data_flow_api

    def get_authenticators(self):
        if self.request.method == 'POST':
            return [PaaSIPAuthentication(), HawkAuthentication()]
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [HawkScopePermission()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateEYBLeadSerializer
        return RetrieveEYBLeadSerializer

    def get_queryset(self):
        """Apply filters to queryset based on query parameters (in GET operations)."""
        queryset = super().get_queryset()
        company_name = self.request.query_params.get('company')
        sector_ids = self.request.query_params.getlist('sector')
        values = self.request.query_params.getlist('value')

        if company_name:
            queryset = queryset.filter(company__name__icontains=company_name)
        if sector_ids:
            try:
                # This will be a list of level 0 sector ids;
                # We want to find and return all leads with sectors that have these ancestors
                descendent_sectors = []
                for sector in Sector.objects.filter(pk__in=sector_ids):
                    descendent_sectors.extend(sector.get_descendants(include_self=True))
                queryset = queryset.filter(sector__in=descendent_sectors)
            except Exception:
                queryset = queryset.none()
        if values:
            value_mappings = {
                'high': True,
                'low': False,
            }
            booleans_to_filter_by = []
            for value in values:
                value_string = value.lower().strip()
                if value_string in value_mappings.keys():
                    booleans_to_filter_by.append(value_mappings[value_string])
            queryset = queryset.filter(is_high_value__in=booleans_to_filter_by)

        return queryset

    def create(self, request):
        """POST route definition.

        This route needs to handle both creating new and updating existing instances
        because data is received automatically from a Data Flow pipeline.

        To reduce complexity of the pipeline, it was decided to have the separation
        logic within the API endpoint.
        """
        if not isinstance(request.data, list) or len(request.data) == 0:
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
                instance, created = self.perform_create_or_update(serializer)
                if created:
                    created_leads.append(serializer.to_representation(instance))
                else:
                    updated_leads.append(serializer.to_representation(instance))
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

    def perform_create_or_update(self, serializer):
        """Processes a single lead.

        The `triage_hashed_uuid` and `user_hashed_uuid` field should be unique for each EYBLead
        instance. As a result, we use these to determine if a new instance is created, or an
        existing one updated.
        """
        validated_lead_data = serializer.validated_data
        lead_instance, created = EYBLead.objects.update_or_create(
            triage_hashed_uuid=validated_lead_data.get('triage_hashed_uuid'),
            user_hashed_uuid=validated_lead_data.get('user_hashed_uuid'),
            defaults=validated_lead_data,
        )
        return lead_instance, created
