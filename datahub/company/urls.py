"""Company views URL config."""

from django.conf.urls import url

from .views import ContactViewSetV3


# CONTACT

contact_collection = ContactViewSetV3.as_view({
    'get': 'list',
    'post': 'create'
})

contact_item = ContactViewSetV3.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

contact_archive = ContactViewSetV3.as_view({
    'post': 'archive',
    'get': 'unarchive'
})


contact_urls_v3 = [
    url(r'^contact$', contact_collection, name='list'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})$', contact_item, name='detail'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/archive$', contact_archive, name='archive'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/unarchive$', contact_archive, name='unarchive'),
]
