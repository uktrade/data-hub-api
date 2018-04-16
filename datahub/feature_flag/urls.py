from django.urls import path

from datahub.feature_flag.views import get_feature_flags

urlpatterns = [
    path('feature-flag', get_feature_flags, name='collection'),
]
