from django.urls import path

from datahub.dataset.views import ContactsDatasetView, InteractionsDatasetView, OMISDatasetView


urlpatterns = [
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
    path('contacts-dataset', ContactsDatasetView.as_view(), name='contacts-dataset'),
    path(
        'service-deliveries-and-interactions-dataset',
        InteractionsDatasetView.as_view(),
        name='interactions-dataset',
    ),
]
