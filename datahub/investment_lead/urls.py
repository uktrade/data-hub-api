from django.urls import path

from datahub.investment_lead.views import EYBLeadViewSet, EYBLeadAuditViewSet


eyb_lead_collection = EYBLeadViewSet.as_view({
    'get': 'list',
})

eyb_lead_item = EYBLeadViewSet.as_view({
    'get': 'retrieve',
})

audit_item = EYBLeadAuditViewSet.as_view({
    'get': 'list',
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
    path(
        'eyb/<uuid:pk>/audit',
        audit_item,
        name='audit-item',
    ),
]
