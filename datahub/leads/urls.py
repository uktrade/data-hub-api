"""Investment views URL config."""

from django.urls import path

from datahub.leads.views import BusinessLeadViewSet

lead_collection = BusinessLeadViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

lead_item = BusinessLeadViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

archive_lead_item = BusinessLeadViewSet.as_view({
    'post': 'archive',
})

unarchive_lead_item = BusinessLeadViewSet.as_view({
    'post': 'unarchive',
})

urlpatterns = [
    path('business-leads', lead_collection, name='lead-collection'),
    path('business-leads/<uuid:pk>', lead_item, name='lead-item'),
    path('business-leads/<uuid:pk>/archive', archive_lead_item, name='archive-lead-item'),
    path('business-leads/<uuid:pk>/unarchive', unarchive_lead_item, name='unarchive-lead-item'),
]
