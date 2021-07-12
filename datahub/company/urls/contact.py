from django.urls import path

from datahub.company.views import ContactAuditViewSet, ContactViewSet

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
