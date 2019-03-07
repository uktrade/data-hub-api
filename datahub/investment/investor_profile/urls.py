from django.urls import path

from datahub.investment.investor_profile.views import LargeCapitalInvestorProfileViewSet

GET_AND_POST_COLLECTION = {
    'get': 'list',
    'post': 'create',
}

GET_AND_PATCH_ITEM = {
    'get': 'retrieve',
    'patch': 'partial_update',
}

collection = LargeCapitalInvestorProfileViewSet.as_view(actions=GET_AND_POST_COLLECTION)

item = LargeCapitalInvestorProfileViewSet.as_view(actions=GET_AND_PATCH_ITEM)

urlpatterns = [
    path('large-investor-profile', collection, name='collection'),
    path('large-investor-profile/<uuid:pk>', item, name='item'),
]
