from django.urls import path

from datahub.datasets.views import OMISDatasetView

urlpatterns = [
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
]
