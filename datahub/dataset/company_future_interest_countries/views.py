from rest_framework.views import APIView

from config.settings.types import HawkScope
from datahub.company.models import Company
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.dataset.company_future_interest_countries.pagination import \
    CompanyFutureInterestCountriesDatasetViewCursorPagination


class CompanyFutureInterestCountriesDatasetView(HawkResponseSigningMixin, APIView):
    """
    A GET API view to return the data for all company future countries of interest 
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    authentication_classes = (HawkAuthentication, )
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.data_flow_api
    pagination_class = CompanyFutureInterestCountriesDatasetViewCursorPagination

    def get(self, request):
        """Endpoint which serves all records for the Companies Dataset"""
        dataset = self.get_dataset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        return paginator.get_paginated_response(page)

    def get_dataset(self):
        """Returns list of Company records"""
        return Company.objects.values('id', 'future_interest_countries')

    
        # return Company.objects.annotate(
        #     sector_name=get_sector_name_subquery('sector'),
        # ).values(
        #     'address_1',
        #     'address_2',
        #     'address_county',
        #     'address_postcode',
        #     'address_town',
        #     'business_type__name',
        #     'company_number',
        #     'created_on',
        #     'description',
        #     'duns_number',
        #     'export_experience_category__name',
        #     'id',
        #     'is_number_of_employees_estimated',
        #     'is_turnover_estimated',
        #     'name',
        #     'number_of_employees',
        #     'one_list_tier__name',
        #     'reference_code',
        #     'registered_address_1',
        #     'registered_address_2',
        #     'registered_address_country__name',
        #     'registered_address_county',
        #     'registered_address_postcode',
        #     'registered_address_town',
        #     'sector_name',
        #     'trading_names',
        #     'turnover',
        #     'uk_region__name',
        #     'vat_number',
        #     'website',
        # )
