from django.urls import path

from datahub.investment.opportunity.views import (
    LargeCapitalOpportunityAuditViewSet,
    LargeCapitalOpportunityViewSet,
)

GET_AND_POST_COLLECTION = {
    'get': 'list',
    'post': 'create',
}

GET_AND_PATCH_ITEM = {
    'get': 'retrieve',
    'patch': 'partial_update',
}


collection = LargeCapitalOpportunityViewSet.as_view(actions=GET_AND_POST_COLLECTION)

item = LargeCapitalOpportunityViewSet.as_view(actions=GET_AND_PATCH_ITEM)

item_audit = LargeCapitalOpportunityAuditViewSet.as_view({
    'get': 'list',
})


urlpatterns = [
    path('large-capital-opportunity', collection, name='collection'),
    path('large-capital-opportunity/<uuid:pk>', item, name='item'),
    path('large-capital-opportunity/<uuid:pk>/audit', item_audit, name='audit-item'),
]
