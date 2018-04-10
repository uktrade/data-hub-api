from django.urls import path

from datahub.featureflag.views import FeatureFlagViewSet

collection = FeatureFlagViewSet.as_view({
    'get': 'list',
})

urlpatterns = [
    path('featureflag', collection, name='collection'),
]
