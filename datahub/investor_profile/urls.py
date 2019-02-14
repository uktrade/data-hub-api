from django.urls import path

from datahub.investor_profile.views import LargeCapitalInvestorProfileViewSet

collection = LargeCapitalInvestorProfileViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

item = LargeCapitalInvestorProfileViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

urlpatterns = [
    path('large-investor-profile', collection, name='collection'),
    path('large-investor-profile/<uuid:pk>', item, name='item'),
]
