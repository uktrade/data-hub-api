from django.urls import path

from datahub.investment_lead.views import EYBLeadViewSet


eyb_lead_collection = EYBLeadViewSet.as_view({
    'post': 'create',
    'get': 'list',
})

eyb_lead_item = EYBLeadViewSet.as_view({
    'get': 'retrieve',
})

urlpatterns = [
    path(
        'eyb',
        eyb_lead_collection,
        name='eyb-lead-collection',
    ),
    path(
        'eyb/<uuid:pk>',
        eyb_lead_item,
        name='eyb-lead-item',
    ),
]
