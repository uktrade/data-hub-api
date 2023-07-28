from django.urls import path

from datahub.company.views import ObjectiveV4ViewSet


Objective_v4_collection = ObjectiveV4ViewSet.as_view(
    {
        'get': 'list',
        'post': 'create',
    }
)

Objective_v4_item = ObjectiveV4ViewSet.as_view(
    {
        'get': 'retrieve',
        'patch': 'partial_update',
    }
)

urls_v4 = [
    path('company/<company_id>/objective', Objective_v4_collection, name='list'),
    path('company/<company_id>/objective/<uuid:pk>', Objective_v4_item, name='detail'),
]
