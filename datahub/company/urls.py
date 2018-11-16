"""Company views URL config."""

from django.urls import path

from datahub.company.timeline.views import CompanyTimelineViewSet
from datahub.company.views import (
    CompaniesHouseCompanyViewSet,
    CompanyAuditViewSet,
    CompanyViewSet,
    ContactAuditViewSet,
    ContactViewSet,
    GroupCoreTeamViewSet,
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

company_collection = CompanyViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

company_item = CompanyViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

company_audit = CompanyAuditViewSet.as_view({
    'get': 'list',
})

company_timeline = CompanyTimelineViewSet.as_view({
    'get': 'list',
})

company_archive = CompanyViewSet.as_view({
    'post': 'archive',
})

company_unarchive = CompanyViewSet.as_view({
    'post': 'unarchive',
})

company_core_team = GroupCoreTeamViewSet.as_view({
    'get': 'list',
})

ch_company_list = CompaniesHouseCompanyViewSet.as_view({
    'get': 'list',
})

ch_company_item = CompaniesHouseCompanyViewSet.as_view({
    'get': 'retrieve',
})

company_urls = [
    path('company', company_collection, name='collection'),
    path('company/<uuid:pk>', company_item, name='item'),
    path('company/<uuid:pk>/archive', company_archive, name='archive'),
    path('company/<uuid:pk>/unarchive', company_unarchive, name='unarchive'),
    path('company/<uuid:pk>/audit', company_audit, name='audit-item'),
    path('company/<uuid:pk>/timeline', company_timeline, name='timeline-collection'),
    path('company/<uuid:pk>/core-team', company_core_team, name='core-team'),
]

ch_company_urls = [
    path('ch-company', ch_company_list, name='collection'),
    path('ch-company/<company_number>', ch_company_item, name='item'),
]
