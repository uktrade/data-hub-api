from django.urls import path

from datahub.dataset.views import OMISDatasetView


urlpatterns = [
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
]
