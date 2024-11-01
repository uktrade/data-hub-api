import logging

from django.db.models import Q

from rest_framework import filters

from datahub.core.viewsets import SoftDeleteCoreViewSet
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import RetrieveEYBLeadSerializer
from datahub.metadata.models import Sector


logger = logging.getLogger(__name__)


class EYBLeadViewSet(SoftDeleteCoreViewSet):
    serializer_class = RetrieveEYBLeadSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_on']

    def get_queryset(self):
        """Apply filters to queryset based on query parameters (in GET operations)."""
        queryset = EYBLead.objects.filter(archived=False).exclude(
            Q(user_hashed_uuid='') | Q(triage_hashed_uuid=''),
        )
        country_ids = self.request.query_params.getlist('country')
        company_name = self.request.query_params.get('company')
        sector_ids = self.request.query_params.getlist('sector')
        values = self.request.query_params.getlist('value')

        if country_ids:
            queryset = queryset.filter(address_country__id__in=country_ids)
        if company_name:
            queryset = queryset.filter(company__name__icontains=company_name)
        if sector_ids:
            # This will be a list of level 0 sector ids;
            # We want to find and return all leads with sectors that have these ancestors
            descendent_sectors = []
            for sector in Sector.objects.filter(pk__in=sector_ids):
                descendent_sectors.extend(sector.get_descendants(include_self=True))
            queryset = queryset.filter(sector__in=descendent_sectors)
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
