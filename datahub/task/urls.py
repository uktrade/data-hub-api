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

# task_v4_tasks_companies_and_projects = TaskV4ViewSet.as_view(
#     {
#         'get': 'list',
#     },
# )

urls_v4 = [
    path('task', Task_v4_collection, name='collection'),
    path('task/<uuid:pk>', Task_v4_item, name='item'),
    path('task/<uuid:pk>/archive', task_archive, name='task_archive'),
    path(
        'task/companies-and-projects',
        get_tasks_companies_and_projects,
        name='task_companies_and_projects'
        ),

]
