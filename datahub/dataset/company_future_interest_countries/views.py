from django.db.models import F
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
        """Endpoint which serves all records for the Company Future Interest Countries dataset"""
        dataset = self.get_dataset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        return paginator.get_paginated_response(page)

    def get_dataset(self):
        """Returns list of Company Future Interest Countries  records"""
        return Company.objects.annotate(
            country_name=F('future_interest_countries__name'),
            iso_alpha2_code=F('future_interest_countries__iso_alpha2_code'),
        ).values(
            'id',
            'country_name',
            'iso_alpha2_code',
        )
