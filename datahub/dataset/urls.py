from django.urls import path

from datahub.dataset.views import ContactsDatasetView, OMISDatasetView


urlpatterns = [
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
    path('contacts-dataset', ContactsDatasetView.as_view(), name='contacts-dataset'),
]
