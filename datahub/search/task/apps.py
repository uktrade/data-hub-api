from datahub.search.apps import SearchApp
from datahub.search.task.models import Task
from datahub.task.models import Task as DBTask
from datahub.task.models import TaskPermission


class TaskSearchApp(SearchApp):
    """SearchApp for task."""

    name = 'task'
    search_model = Task
    view_permissions = (f'task.{TaskPermission.view_task}',)
    queryset = (
        DBTask.objects.all()
        .select_related(
            'created_by',
            'investment_project',
            'interaction',
        )
        .prefetch_related(
            'advisers',
        )
    )
