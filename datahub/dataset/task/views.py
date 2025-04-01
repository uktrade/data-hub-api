from django.contrib.postgres.aggregates import ArrayAgg

from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.utils import filter_data_by_modified_date
from datahub.task.models import Task


class TasksDatasetView(BaseFilterDatasetView):
    """A GET API view to return the data for recently modified tasks."""

    def get_dataset(self, request):
        """Returns queryset of Task records."""
        queryset = Task.objects.annotate(
            adviser_ids=ArrayAgg(
                'advisers__id',
                ordering=[
                    'advisers__first_name',
                    'advisers__id',
                ],
            ),
        ).values(
            'created_on',
            'created_by_id',
            'modified_on',
            'modified_by_id',
            'archived',
            'archived_on',
            'archived_by_id',
            'archived_reason',
            'id',
            'title',
            'description',
            'due_date',
            'reminder_days',
            'email_reminders_enabled',
            'adviser_ids',
            'reminder_date',
            'investment_project_id',
            'company_id',
            'interaction_id',
            'status',
        )
        updated_since = request.GET.get('updated_since')
        filtered_queryset = filter_data_by_modified_date(updated_since, queryset)
        return filtered_queryset
