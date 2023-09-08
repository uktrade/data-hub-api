from django.urls import path

from datahub.task.views import TaskV4ViewSet


Task_v4_item = TaskV4ViewSet.as_view(
    {
        'get': 'retrieve',
    },
)

Task_v4_collection = TaskV4ViewSet.as_view(
    {
        'get': 'list',
    },
)

urls_v4 = [
    path('task', Task_v4_collection, name='collection'),
    path('task/<uuid:pk>', Task_v4_item, name='item'),
]
