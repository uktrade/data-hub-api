from datetime import datetime

from django.contrib.postgres.aggregates import ArrayAgg

from datahub.company.models import Company
from datahub.dataset.core.views import BaseDatasetView
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.metadata.utils import convert_usd_to_gbp


def parse_date(value):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class CompaniesDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all companies as required
    for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    def get(self, request):
        """Endpoint which serves all records for Company Dataset"""
        dataset = self.get_dataset(request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        self._enrich_data(page)
        return paginator.get_paginated_response(page)

    def get_dataset(self, request):
        """Returns list of Company records"""
        queryset = Company.objects.annotate(
            sector_name=get_sector_name_subquery('sector'),
            one_list_core_team_advisers=ArrayAgg('one_list_core_team_members__adviser_id'),
        ).values(
            'address_1',
            'address_2',
            'address_county',
            'address_country__name',
            'address_postcode',
            'address_area__name',
            'address_town',
            'archived',
            'archived_on',
            'archived_reason',
            'business_type__name',
            'company_number',
            'created_by_id',
            'created_on',
            'description',
            'duns_number',
            'export_experience_category__name',
            'global_headquarters_id',
            'global_ultimate_duns_number',
            'headquarter_type__name',
            'id',
            'is_number_of_employees_estimated',
            'is_turnover_estimated',
            'modified_on',
            'name',
            'number_of_employees',
            'one_list_account_owner_id',
            'one_list_tier__name',
            'one_list_core_team_advisers',
            'reference_code',
            'registered_address_1',
            'registered_address_2',
            'registered_address_country__name',
            'registered_address_county',
            'registered_address_postcode',
            'registered_address_area__name',
            'registered_address_town',
            'sector_name',
            'export_segment',
            'export_sub_segment',
            'trading_names',
            'turnover',
            'uk_region__name',
            'vat_number',
            'website',
            'is_out_of_business',
            'strategy',
        )
        updated_since = request.GET.get('updated_since')
        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(created_on__gt=updated_since_date)

        return queryset

    def _enrich_data(self, dataset):
        for data in dataset:
            if data.get('turnover') is not None:
                data['turnover_gbp'] = convert_usd_to_gbp(data['turnover'])
            else:
                data['turnover_gbp'] = None
        return super()._enrich_data(dataset)
