from django.urls import path

from datahub.company.timeline.views import CompanyTimelineViewSet
from datahub.company.views import (
    CompanyAuditViewSet,
    CompanyViewSet,
    OneListGroupCoreTeamViewSet,
    PublicCompanyViewSet,
)


company_collection_v4 = CompanyViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

company_item_v4 = CompanyViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

company_audit = CompanyAuditViewSet.as_view({
    'get': 'list',
})

company_timeline = CompanyTimelineViewSet.as_view({
    'get': 'list',
})

company_archive_v4 = CompanyViewSet.as_view({
    'post': 'archive',
})

company_unarchive_v4 = CompanyViewSet.as_view({
    'post': 'unarchive',
})

one_list_group_core_team = OneListGroupCoreTeamViewSet.as_view({
    'get': 'list',
})

public_company_item_v4 = PublicCompanyViewSet.as_view({
    'get': 'retrieve',
})

urls_v4 = [
    path('company', company_collection_v4, name='collection'),
    path('company/<uuid:pk>', company_item_v4, name='item'),
    path('company/<uuid:pk>/archive', company_archive_v4, name='archive'),
    path('company/<uuid:pk>/unarchive', company_unarchive_v4, name='unarchive'),
    path('company/<uuid:pk>/audit', company_audit, name='audit-item'),
    path('company/<uuid:pk>/timeline', company_timeline, name='timeline-collection'),
    path(
        'company/<uuid:pk>/one-list-group-core-team',
        one_list_group_core_team,
        name='one-list-group-core-team',
    ),
    path('public/company/<uuid:pk>', public_company_item_v4, name='public-item'),
]
