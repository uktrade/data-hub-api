from datahub.search.apps import SearchApp
from datahub.search.task.models import Task
from datahub.task.models import Task as DBTask, TaskPermission


class TaskSearchApp(SearchApp):
    """SearchApp for task."""

    name = 'task'
    search_model = Task
    view_permissions = (f'task.{TaskPermission.view_task}',)
    queryset = DBTask.objects.all().select_related(
        'investment_project',
        'interaction',
    )
