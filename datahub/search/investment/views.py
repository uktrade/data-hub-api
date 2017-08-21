from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InvestmentProject
from .. import elasticsearch


class SearchInvestmentProjectAPIView(APIView):
    """Filtered investment project search view."""

    SORT_BY_FIELDS = (
        'actual_land_date',
        'approved_commitment_to_invest',
        'approved_fdi',
        'approved_good_value',
        'approved_high_value',
        'approved_landed',
        'approved_non_fdi',
        'archived',
        'archived_by.name',
        'average_salary.name',
        'business_activities.name',
        'client_cannot_provide_total_investment',
        'client_contacts.name',
        'client_relationship_manager.name',
        'created_on',
        'estimated_land_date',
        'export_revenue',
        'fdi_type.name',
        'foreign_equity_investment',
        'government_assistance',
        'id',
        'intermediate_company.name',
        'investment_type.name',
        'investor_company.name',
        'modified_on',
        'name',
        'nda_signed',
        'new_tech_to_uk',
        'non_fdi_r_and_d_budget',
        'non_fdi_type.name',
        'number_new_jobs',
        'project_assurance_adviser.name',
        'project_code',
        'project_manager.name',
        'project_shareable',
        'r_and_d_budget',
        'referral_source_activity.name',
        'referral_source_activity_event',
        'referral_source_activity_marketing.name',
        'referral_source_activity_website.name',
        'referral_source_advisor.name',
        'sector.name',
        'site_decided',
        'stage.name',
        'team_members.name',
        'total_investment',
        'uk_company.name'
    )

    FILTER_FIELDS = (
        'client_relationship_manager',
        'estimated_land_date_after',
        'estimated_land_date_before',
        'investment_type',
        'investor_company',
        'sector',
        'stage'
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered contact search."""
        filters = {elasticsearch.remap_filter_id_field(field): request.data[field]
                   for field in self.FILTER_FIELDS if field in request.data}
        try:
            filters, ranges = elasticsearch.date_range_fields(filters)
        except ValueError:
            raise ValidationError('Date(s) in incorrect format.')

        original_query = request.data.get('original_query', '')

        sortby = request.data.get('sortby')
        if sortby:
            field = sortby.rsplit(':')[0]
            if field not in self.SORT_BY_FIELDS:
                raise ValidationError(f'"sortby" field is not one of {self.SORT_BY_FIELDS}.')

        offset = int(request.data.get('offset', 0))
        limit = int(request.data.get('limit', 100))

        results = elasticsearch.get_search_by_entity_query(
            entity=InvestmentProject,
            term=original_query,
            filters=filters,
            ranges=ranges,
            field_order=sortby,
            aggs=self.FILTER_FIELDS,
            offset=offset,
            limit=limit,
        ).execute()

        aggregations = {}
        for field in self.FILTER_FIELDS:
            es_field = elasticsearch.remap_filter_id_field(field)
            if es_field in results.aggregations:
                aggregation = results.aggregations[es_field]
                if '.' in es_field:
                    aggregation = aggregation[es_field]

                aggregations[field] = [bucket.to_dict() for bucket in aggregation['buckets']]

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
            'aggregations': aggregations,
        }

        return Response(data=response)
