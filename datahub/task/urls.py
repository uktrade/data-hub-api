from django.urls import path

from datahub.task.views import TaskV4ViewSet


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

contact_archive = TaskV4ViewSet.as_action_view('archive')

urls_v4 = [
    path('task', Task_v4_collection, name='collection'),
    path('task/<uuid:pk>', Task_v4_item, name='item'),
    path('task/<uuid:pk>/archive', contact_archive, name='task_archive'),
]