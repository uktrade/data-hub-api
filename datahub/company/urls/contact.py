from django.urls import path

from datahub.company.views import ContactAuditViewSet, ContactViewSet, ContactViewSetV4

contact_collection = ContactViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

contact_item = ContactViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

contact_archive = ContactViewSet.as_action_view('archive')

contact_unarchive = ContactViewSet.as_action_view('unarchive')

contact_audit = ContactAuditViewSet.as_view({
    'get': 'list',
})

urls_v3 = [
    path('contact', contact_collection, name='list'),
    path('contact/<uuid:pk>', contact_item, name='detail'),
    path('contact/<uuid:pk>/archive', contact_archive, name='archive'),
    path('contact/<uuid:pk>/unarchive', contact_unarchive, name='unarchive'),
    path('contact/<uuid:pk>/audit', contact_audit, name='audit-item'),
]

contact_collection_v4 = ContactViewSetV4.as_view({
    'get': 'list',
    'post': 'create',
})

contact_item_v4 = ContactViewSetV4.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

contact_archive_v4 = ContactViewSetV4.as_action_view('archive')

contact_unarchive_v4 = ContactViewSetV4.as_action_view('unarchive')

urls_v4 = [
    path('contact', contact_collection_v4, name='list'),
    path('contact/<uuid:pk>', contact_item_v4, name='detail'),
    path('contact/<uuid:pk>/archive', contact_archive_v4, name='archive'),
    path('contact/<uuid:pk>/unarchive', contact_unarchive_v4, name='unarchive'),
]
