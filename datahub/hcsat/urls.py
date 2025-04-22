from django.urls import path

from datahub.hcsat.views import CustomerSatisfactionToolFeedbackViewSet

hcsat_collection = CustomerSatisfactionToolFeedbackViewSet.as_view({
    'post': 'create',
})

hcsat_item = CustomerSatisfactionToolFeedbackViewSet.as_view({
    'patch': 'partial_update',
})

urls_v4 = [
    path('hcsat', hcsat_collection, name='collection'),
    path('hcsat/<uuid:pk>', hcsat_item, name='item'),
]
