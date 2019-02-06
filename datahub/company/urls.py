"""Company views URL config."""

from django.urls import path

from datahub.company.timeline.views import CompanyTimelineViewSet
from datahub.company.views import (
    CompaniesHouseCompanyViewSet,
    CompanyAuditViewSet,
    CompanyViewSetV3,
    ContactAuditViewSet,
    ContactViewSet,
    OneListGroupCoreTeamViewSet,
)

# CONTACT

contact_collection = ContactViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

contact_item = ContactViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

contact_archive = ContactViewSet.as_view({
    'post': 'archive',
})

contact_unarchive = ContactViewSet.as_view({
    'post': 'unarchive',
})

contact_audit = ContactAuditViewSet.as_view({
    'get': 'list',
})

contact_urls = [
    path('contact', contact_collection, name='list'),
    path('contact/<uuid:pk>', contact_item, name='detail'),
    path('contact/<uuid:pk>/archive', contact_archive, name='archive'),
    path('contact/<uuid:pk>/unarchive', contact_unarchive, name='unarchive'),
    path('contact/<uuid:pk>/audit', contact_audit, name='audit-item'),
]

# COMPANY

company_collection_v3 = CompanyViewSetV3.as_view({
    'get': 'list',
    'post': 'create',
})

company_item_v3 = CompanyViewSetV3.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

company_audit = CompanyAuditViewSet.as_view({
    'get': 'list',
})

company_timeline = CompanyTimelineViewSet.as_view({
    'get': 'list',
})

company_archive_v3 = CompanyViewSetV3.as_view({
    'post': 'archive',
})

company_unarchive_v3 = CompanyViewSetV3.as_view({
    'post': 'unarchive',
})

one_list_group_core_team = OneListGroupCoreTeamViewSet.as_view({
    'get': 'list',
})

ch_company_list = CompaniesHouseCompanyViewSet.as_view({
    'get': 'list',
})

ch_company_item = CompaniesHouseCompanyViewSet.as_view({
    'get': 'retrieve',
})

company_urls_v3 = [
    path('company', company_collection_v3, name='collection'),
    path('company/<uuid:pk>', company_item_v3, name='item'),
    path('company/<uuid:pk>/archive', company_archive_v3, name='archive'),
    path('company/<uuid:pk>/unarchive', company_unarchive_v3, name='unarchive'),
    path('company/<uuid:pk>/audit', company_audit, name='audit-item'),
    path('company/<uuid:pk>/timeline', company_timeline, name='timeline-collection'),
    path(
        'company/<uuid:pk>/one-list-group-core-team',
        one_list_group_core_team,
        name='one-list-group-core-team',
    ),
]

ch_company_urls = [
    path('ch-company', ch_company_list, name='collection'),
    path('ch-company/<company_number>', ch_company_item, name='item'),
]
