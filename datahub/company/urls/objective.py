from django.urls import path

from datahub.company.views import (
    CompanyObjectiveArchivedCountV4ViewSet,
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

objective_archive = SingleObjectiveV4ViewSet.as_action_view('archive')

urls_v4 = [
    path('company/<uuid:company_id>/objective', Objective_v4_collection, name='list'),
    path(
        'company/<uuid:company_id>/objective/count',
        CompanyObjectiveArchivedCountV4ViewSet.as_view(),
        name='count',
    ),
    path('company/<uuid:company_id>/objective/<uuid:pk>', Objective_v4_item, name='detail'),
    path(
        'company/objective/<uuid:pk>/archive',
        objective_archive,
        name='archive',
    ),
]
