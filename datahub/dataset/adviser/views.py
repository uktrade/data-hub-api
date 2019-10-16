from rest_framework.views import APIView

from config.settings.types import HawkScope
from datahub.company.models.adviser import Advisor as Adviser
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.dataset.adviser.pagination import AdvisersDatasetViewCursorPagination


class AdvisersDatasetView(HawkResponseSigningMixin, APIView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Advisers Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints.
    """

    authentication_classes = (HawkAuthentication, )
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.data_flow_api
    pagination_class = AdvisersDatasetViewCursorPagination

    def get(self, request):
        """Endpoint which serves all records for Advisers Dataset"""
        dataset = self.get_dataset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        return paginator.get_paginated_response(page)

    def get_dataset(self):
        """Returns list of Advisers Dataset records"""
        return Adviser.objects.values(
            'id',
            'date_joined',
            'first_name',
            'last_name',
            'telephone_number',
            'contact_email',
            'dit_team_id',
            'is_active',
        )
