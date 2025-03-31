from django.urls import path

from datahub.task.views import (
    TaskV4ViewSet,
    get_tasks_companies_and_projects,
)

Task_v4_item = TaskV4ViewSet.as_view(
    {
        'get': 'retrieve',
        'patch': 'partial_update',
    },
)

Task_v4_collection = TaskV4ViewSet.as_view(
    {
        'get': 'list',
        'post': 'create',
    },
)

task_archive = TaskV4ViewSet.as_action_view('archive')
task_status_active = TaskV4ViewSet.as_action_view('status_active')
task_status_complete = TaskV4ViewSet.as_action_view('status_complete')

urls_v4 = [
    path('task', Task_v4_collection, name='collection'),
    path('task/<uuid:pk>', Task_v4_item, name='item'),
    path('task/<uuid:pk>/archive', task_archive, name='task_archive'),
    path('task/<uuid:pk>/status-active', task_status_active, name='task_status_active'),
    path('task/<uuid:pk>/status-complete', task_status_complete, name='task_status_complete'),
    path(
        'task/companies-and-projects',
        get_tasks_companies_and_projects,
        name='companies-and-projects',
    ),

]
