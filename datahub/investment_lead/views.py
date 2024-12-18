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

    def _filter_by_overseas_regions(self, queryset):
        overseas_region_ids = self.request.query_params.getlist('overseas_region')
        if overseas_region_ids:
            queryset = queryset.filter(
                address_country__overseas_region__id__in=overseas_region_ids,
            )
        return queryset

    def _filter_by_countries(self, queryset):
        country_ids = self.request.query_params.getlist('country')
        if country_ids:
            queryset = queryset.filter(address_country__id__in=country_ids)
        return queryset

    def _filter_by_company_name(self, queryset):
        company_name = self.request.query_params.get('company')
        if company_name:
            queryset = queryset.filter(
                Q(company__name__icontains=company_name) | Q(company_name__icontains=company_name),
            )
        return queryset

    def _filter_by_sectors(self, queryset):
        sector_ids = self.request.query_params.getlist('sector')
        if sector_ids:
            # This will be a list of level 0 sector ids;
            # We want to find and return all leads with sectors that have these ancestors
            descendent_sectors = []
            for sector in Sector.objects.filter(pk__in=sector_ids):
                descendent_sectors.extend(sector.get_descendants(include_self=True))
            queryset = queryset.filter(sector__in=descendent_sectors)
        return queryset

    def _filter_by_values(self, queryset):
        values = self.request.query_params.getlist('value')
        if values:
            value_mappings = {
                'high': True,
                'low': False,
                'unknown': None,
            }
            values_to_filter_by = []
            has_unknown = False
            for value in values:
                value_string = value.lower().strip()
                if value_string in value_mappings.keys():
                    mapped_value = value_mappings[value_string]
                    if mapped_value is None:
                        has_unknown = True
                    else:
                        values_to_filter_by.append(mapped_value)
            filter_query = Q(is_high_value__in=values_to_filter_by)
            if has_unknown:
                filter_query |= Q(is_high_value__isnull=True)
            queryset = queryset.filter(filter_query)
        return queryset

    def get_queryset(self):
        """Apply filters to queryset based on query parameters (in GET operations)."""
        queryset = EYBLead.objects.filter(archived=False).exclude(
            Q(user_hashed_uuid='') | Q(triage_hashed_uuid=''),
        )

        queryset = self._filter_by_overseas_regions(queryset)
        queryset = self._filter_by_countries(queryset)
        queryset = self._filter_by_company_name(queryset)
        queryset = self._filter_by_sectors(queryset)
        queryset = self._filter_by_values(queryset)

        return queryset
