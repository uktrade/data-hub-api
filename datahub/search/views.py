"""Search views."""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import elasticsearch


class SearchBasicAPIView(APIView):
    """Aggregate company and contact search view."""

    http_method_names = ('get',)

    SORT_BY_FIELDS = (
        'name', 'created_on',
    )

    def get(self, request, format=None):
        """Performs basic search."""
        if 'term' not in request.query_params:
            raise ValidationError('Missing required "term" field.')
        term = request.query_params['term']

        entity = request.query_params.get('entity', 'company')
        if entity not in ('company', 'contact', 'investment_project'):
            raise ValidationError('Entity is not one of "company", "contact" or '
                                  '"investment_project".')

        sortby = request.query_params.get('sortby')
        if sortby:
            field = sortby.rsplit(':')[0]
            if field not in self.SORT_BY_FIELDS:
                raise ValidationError(f'"sortby" field is not one of {self.SORT_BY_FIELDS}.')

        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 100))

        results = elasticsearch.get_basic_search_query(
            term=term,
            entities=entity.split(','),
            field_order=sortby,
            offset=offset,
            limit=limit
        ).execute()

        response = {
            'count': results.hits.total,
            'aggregations': [{'count': x['doc_count'], 'entity': x['key']}
                             for x in results.aggregations['count_by_type']['buckets']],
        }

        hits = [x.to_dict() for x in results.hits]

        if entity == 'company':
            response['companies'] = hits
        elif entity == 'contact':
            response['contacts'] = hits
        elif entity == 'investment_project':
            response['investment_projects'] = hits

        return Response(data=response)


class SearchCompanyAPIView(APIView):
    """Filtered company search view."""

    SORT_BY_FIELDS = (
        'account_manager.name', 'alias', 'archived', 'archived_by',
        'contacts.name', 'business_type.name',
        'classification.name', 'company_number', 'companies_house_data.company_number',
        'created_on', 'employee_range.name', 'headquarter_type.name', 'id', 'modified_on',
        'name', 'registered_address_town', 'sector.name', 'trading_address_town',
        'turnover_range.name', 'uk_region.name', 'uk_based',
        'export_to_countries.name', 'future_interest_countries.name',
    )

    FILTER_FIELDS = (
        'name', 'alias', 'sector', 'account_manager', 'export_to_country',
        'future_interest_country', 'description', 'uk_region', 'uk_based',
        'trading_address_town', 'trading_address_country', 'trading_address_postcode',
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered company search."""
        filters = {elasticsearch.remap_field(field): request.data[field]
                   for field in self.FILTER_FIELDS if field in request.data}

        original_query = request.data.get('original_query', '')

        sortby = request.data.get('sortby')
        if sortby:
            field = sortby.rsplit(':')[0]
            if field not in self.SORT_BY_FIELDS:
                raise ValidationError(f'"sortby" field is not one of {self.SORT_BY_FIELDS}.')

        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 100))

        results = elasticsearch.get_search_company_query(
            term=original_query,
            filters=filters,
            field_order=sortby,
            offset=offset,
            limit=limit,
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
        }

        return Response(data=response)


class SearchContactAPIView(APIView):
    """Filtered contact search view."""

    SORT_BY_FIELDS = (
        'archived', 'archived', 'created_on',
        'modified_on', 'id', 'name', 'title.name', 'primary',
        'telephone_countrycode', 'telephone_number',
        'email', 'address_same_as_company', 'address_town', 'address_county',
        'job_title', 'contactable_by_dit', 'contactable_by_dit_partners', 'contactable_by_email',
        'contactable_by_phone', 'address_country.name', 'adviser.name', 'archived_by.name',
        'company.name',
    )

    FILTER_FIELDS = (
        'first_name', 'last_name', 'job_title', 'company', 'adviser', 'notes',
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered contact search."""
        filters = {elasticsearch.remap_field(field): request.data[field]
                   for field in self.FILTER_FIELDS if field in request.data}

        original_query = request.data.get('original_query', '')

        sortby = request.data.get('sortby')
        if sortby:
            field = sortby.rsplit(':')[0]
            if field not in self.SORT_BY_FIELDS:
                raise ValidationError(f'"sortby" field is not one of {self.SORT_BY_FIELDS}.')

        offset = int(request.data.get('offset', 0))
        limit = int(request.data.get('limit', 100))

        results = elasticsearch.get_search_contact_query(
            term=original_query,
            filters=filters,
            field_order=sortby,
            offset=offset,
            limit=limit,
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
        }

        return Response(data=response)


class SearchInvestmentProjectAPIView(APIView):
    """Filtered investment project search view."""

    SORT_BY_FIELDS = (
        'id', 'approved_commitment_to_invest',
        'approved_fdi', 'approved_good_value',
        'approved_high_value', 'approved_landed',
        'approved_non_fdi', 'actual_land_date',
        'business_activities.name', 'client_contacts.name',
        'client_relationship_manager.name', 'project_manager.name',
        'project_assurance_adviser.name', 'team_members.name',
        'archived', 'archived_by.name', 'created_on', 'modified_on',
        'estimated_land_date', 'fdi_type.name', 'intermediate_company.name',
        'uk_company.name', 'investor_company.name', 'investment_type.name', 'name',
        'r_and_d_budget', 'non_fdi_r_and_d_budget', 'new_tech_to_uk', 'export_revenue',
        'site_decided', 'nda_signed', 'government_assistance',
        'client_cannot_provide_total_investment', 'total_investment',
        'foreign_equity_investment', 'number_new_jobs', 'non_fdi_type.name',
        'stage.name', 'project_code', 'project_shareable',
        'referral_source_activity.name', 'referral_source_activity_marketing.name',
        'referral_source_activity_website.name', 'referral_source_activity_event',
        'referral_source_advisor.name', 'sector.name', 'average_salary.name',
    )

    FILTER_FIELDS = (
        'client_relationship_manager', 'estimated_land_date_after',
        'estimated_land_date_before', 'investor_company', 'investment_type',
        'stage', 'sector'
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered contact search."""
        filters = {elasticsearch.remap_field(field): request.data[field]
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

        results = elasticsearch.get_search_investment_project_query(
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
            es_field = elasticsearch.remap_field(field)
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
