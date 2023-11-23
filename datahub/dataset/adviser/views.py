from datahub.company.models.adviser import Advisor as Adviser
from datahub.dataset.adviser.pagination import AdvisersDatasetViewCursorPagination
from datahub.dataset.core.views import BaseDatasetView
from datahub.dbmaintenance.utils import parse_date


class AdvisersDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Advisers Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints.
    """

    pagination_class = AdvisersDatasetViewCursorPagination

    def get(self, request):
        """Endpoint which serves all records for Advisers Dataset"""
        dataset = self.get_dataset(request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        self._enrich_data(page)
        return paginator.get_paginated_response(page)

    def get_dataset(self, request):
        """Returns list of Advisers Dataset records with optional date filtering"""
        queryset = Adviser.objects.values(
            'id',
            'date_joined',
            'first_name',
            'last_login',
            'last_name',
            'telephone_number',
            'contact_email',
            'dit_team_id',
            'is_active',
            'sso_email_user_id',
        )

        updated_since = request.GET.get('updated_since')

        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset
