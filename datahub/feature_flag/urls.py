from django.urls import path

from datahub.feature_flag.views import FeatureFlagViewSet

collection = FeatureFlagViewSet.as_view({
    'get': 'list',
})

urlpatterns = [
    path('feature-flag', collection, name='collection'),
]
