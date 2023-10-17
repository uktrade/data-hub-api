from django.urls import path


from datahub.task.views import InvestmentProjectTaskV4ViewSet, TaskV4ViewSet


Task_v4_item = TaskV4ViewSet.as_view(
    {
        'get': 'retrieve',
        'patch': 'partial_update',
    },
)
InvestmentProjectTask_v4_item = InvestmentProjectTaskV4ViewSet.as_view(
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
InvestmentProjectTask_v4_collection = InvestmentProjectTaskV4ViewSet.as_view(
    {
        'get': 'list',
        'post': 'create',
    },
)

task_archive = TaskV4ViewSet.as_action_view('archive')

urls_v4 = [
    path('task', Task_v4_collection, name='collection'),
    path('task/<uuid:pk>', Task_v4_item, name='item'),
    path('task/<uuid:pk>/archive', task_archive, name='task_archive'),
    path(
        'investmentprojecttask/<uuid:pk>',
        InvestmentProjectTask_v4_item,
        name='investment_project_task_item',
    ),
    path(
        'investmentprojecttask',
        InvestmentProjectTask_v4_collection,
        name='investment_project_task_collection',
    ),
]
