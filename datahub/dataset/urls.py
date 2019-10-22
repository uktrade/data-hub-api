from django.urls import path

from datahub.dataset.company.views import CompaniesDatasetView
from datahub.dataset.company_future_interest_countries.views import \
    CompanyFutureInterestCountriesDatasetView
from datahub.dataset.contact.views import ContactsDatasetView
from datahub.dataset.interaction.views import InteractionsDatasetView
from datahub.dataset.order.views import OMISDatasetView


urlpatterns = [
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
    path('contacts-dataset', ContactsDatasetView.as_view(), name='contacts-dataset'),
    path('companies-dataset', CompaniesDatasetView.as_view(), name='companies-dataset'),
    path(
        'company-future-interest-countries-dataset',
        CompanyFutureInterestCountriesDatasetView.as_view(),
        name='company-future-interest-countries-dataset',
    ),
    path('interactions-dataset', InteractionsDatasetView.as_view(), name='interactions-dataset'),
]
