"""Company views URL config."""

from django.conf.urls import url

from datahub.company.views import (CompanyViewSetV3, ContactViewSet,
                                   CompaniesHouseCompanyReadOnlyViewSetV1)

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
    # GET will be removed when the FE is no longer using it
    'get': 'unarchive',
    'post': 'unarchive',
})

contact_urls = [
    url(r'^contact$', contact_collection, name='list'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})$', contact_item, name='detail'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/archive$', contact_archive,
        name='archive'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/unarchive$', contact_unarchive,
        name='unarchive'),
]

# COMPANY

company_collection = CompanyViewSetV3.as_view({
    'get': 'list',
    'post': 'create'
})

company_item = CompanyViewSetV3.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

company_archive = CompanyViewSetV3.as_view({
    'post': 'archive'
})

company_unarchive = CompanyViewSetV3.as_view({
    'post': 'unarchive',
})

ch_company_list = CompaniesHouseCompanyReadOnlyViewSetV1.as_view({
    'get': 'list'
})

ch_company_item = CompaniesHouseCompanyReadOnlyViewSetV1.as_view({
    'get': 'retrieve'
})

company_urls = [
    url(r'^company$', company_collection, name='collection'),
    url(r'^company/(?P<pk>[0-9a-z-]{36})$', company_item, name='item'),
    url(r'^company/(?P<pk>[0-9a-z-]{36})/archive$', company_archive,
        name='archive'),
    url(r'^company/(?P<pk>[0-9a-z-]{36})/unarchive$', company_unarchive,
        name='unarchive'),
]

ch_company_urls = [
    url(r'^ch-company$', ch_company_list,
        name='collection'),
    url(r'^ch-company/(?P<pk>[0-9]+)$', ch_company_item,
        name='item'),
]
