from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.hcsat.pagination import HCSATDatasetViewCursorPagination
from datahub.dataset.utils import filter_data_by_modified_date
from datahub.hcsat.models import CustomerSatisfactionToolFeedback


class HCSATDatasetView(BaseFilterDatasetView):
    """An APIView that provides 'get' action which queries and returns desired
    fields for Customer Satisfaction Tool Feedback Dataset to be consumed by
    data-flow periodically, which uses response results to insert data into
    Data Workspace through its defined API endpoints.
    """

    pagination_class = HCSATDatasetViewCursorPagination

    def get_dataset(self, request):
        queryset = CustomerSatisfactionToolFeedback.objects.values(
            'id',
            'created_on',
            'modified_on',
            'url',
            'was_useful',
            'did_not_find_what_i_wanted',
            'difficult_navigation',
            'lacks_feature',
            'unable_to_load',
            'inaccurate_information',
            'other_issues',
            'other_issues_detail',
            'improvement_suggestion',
        )

        updated_since = request.GET.get('updated_since')
        filtered_queryset = filter_data_by_modified_date(updated_since, queryset)

        return filtered_queryset
