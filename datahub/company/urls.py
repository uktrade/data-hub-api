"""Company views URL config."""

from django.conf.urls import url

from datahub.company.views import (
    CompaniesHouseCompanyViewSet, CompanyAuditViewSet, CompanyViewSet,
    ContactAuditViewSet, ContactViewSet
)

# CONTACT

contact_collection = ContactViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

contact_item = ContactViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

contact_archive = ContactViewSet.as_view({
    'post': 'archive'
})

contact_unarchive = ContactViewSet.as_view({
    'post': 'unarchive',
})

contact_audit = ContactAuditViewSet.as_view({
    'get': 'list',
})

contact_urls = [
    url(r'^contact$', contact_collection, name='list'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})$', contact_item, name='detail'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/archive$', contact_archive,
        name='archive'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/unarchive$', contact_unarchive,
        name='unarchive'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/audit$', contact_audit,
        name='audit-item'),
]

# COMPANY

company_collection = CompanyViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

company_item = CompanyViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

company_audit = CompanyAuditViewSet.as_view({
    'get': 'list',
})

company_archive = CompanyViewSet.as_view({
    'post': 'archive'
})

company_unarchive = CompanyViewSet.as_view({
    'post': 'unarchive',
})

ch_company_list = CompaniesHouseCompanyViewSet.as_view({
    'get': 'list'
})

ch_company_item = CompaniesHouseCompanyViewSet.as_view({
    'get': 'retrieve'
})

company_urls = [
    url(r'^company$', company_collection, name='collection'),
    url(r'^company/(?P<pk>[0-9a-z-]{36})$', company_item, name='item'),
    url(r'^company/(?P<pk>[0-9a-z-]{36})/archive$', company_archive,
        name='archive'),
    url(r'^company/(?P<pk>[0-9a-z-]{36})/unarchive$', company_unarchive,
        name='unarchive'),
    url(r'^company/(?P<pk>[0-9a-z-]{36})/audit$', company_audit,
        name='audit-item'),
]

ch_company_urls = [
    url(r'^ch-company$', ch_company_list,
        name='collection'),
    url(r'^ch-company/(?P<company_number>[\w]+)$', ch_company_item,
        name='item'),
]
