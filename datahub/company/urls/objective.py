from django.urls import path

from datahub.company.views import (
    CompanyObjectiveCountV4ViewSet,
    CompanyObjectiveV4ViewSet,
    SingleObjectiveV4ViewSet,
)


Objective_v4_collection = CompanyObjectiveV4ViewSet.as_view(
    {
        'get': 'list',
        'post': 'create',
    },
)

Objective_v4_item = SingleObjectiveV4ViewSet.as_view(
    {
        'get': 'retrieve',
        'patch': 'partial_update',
    },
)


urls_v4 = [
    path('company/<uuid:company_id>/objective', Objective_v4_collection, name='list'),
    path(
        'company/<uuid:company_id>/objective/count',
        CompanyObjectiveCountV4ViewSet.as_view(),
        name='count',
    ),
    path('company/<uuid:company_id>/objective/<uuid:pk>', Objective_v4_item, name='detail'),
]
