from django.urls import path

from datahub.dataset.contact.views import ContactsDatasetView
from datahub.dataset.order.views import OMISDatasetView


urlpatterns = [
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
    path('contacts-dataset', ContactsDatasetView.as_view(), name='contacts-dataset'),
]
