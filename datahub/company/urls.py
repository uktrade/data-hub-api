"""Company views URL config."""

from django.conf.urls import url

from .views import ContactViewSet


# CONTACT

contact_collection = ContactViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

contact_item = ContactViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update'
})

contact_archive = ContactViewSet.as_view({
    'post': 'archive',
    'get': 'unarchive'
})


contact_urls = [
    url(r'^contact$', contact_collection, name='list'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})$', contact_item, name='detail'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/archive$', contact_archive, name='archive'),
    url(r'^contact/(?P<pk>[0-9a-z-]{36})/unarchive$', contact_archive, name='unarchive'),
]
