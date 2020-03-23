from django.urls import path

from datahub.dataset.adviser.views import AdvisersDatasetView
from datahub.dataset.company.views import CompaniesDatasetView
from datahub.dataset.company_export_country_history.views import (
    CompanyExportCountryHistoryDatasetView,
)
from datahub.dataset.company_export_to_country.views import (
    CompanyExportToCountriesDatasetView,
)
from datahub.dataset.company_future_interest_countries.views import (
    CompanyFutureInterestCountriesDatasetView,
)
from datahub.dataset.contact.views import ContactsDatasetView
from datahub.dataset.event.views import EventsDatasetView
from datahub.dataset.interaction.views import InteractionsDatasetView
from datahub.dataset.interaction_export_country.views import InteractionsExportCountryDatasetView
from datahub.dataset.investment_project.views import (
    InvestmentProjectsActivityDatasetView,
    InvestmentProjectsDatasetView,
)
from datahub.dataset.order.views import OMISDatasetView
from datahub.dataset.team.views import TeamsDatasetView


urlpatterns = [
    path('advisers-dataset', AdvisersDatasetView.as_view(), name='advisers-dataset'),
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
    path('contacts-dataset', ContactsDatasetView.as_view(), name='contacts-dataset'),
    path('companies-dataset', CompaniesDatasetView.as_view(), name='companies-dataset'),
    path(
        'company-export-country-history-dataset',
        CompanyExportCountryHistoryDatasetView.as_view(),
        name='company-export-country-history-dataset',
    ),
    path(
        'company-export-to-countries-dataset',
        CompanyExportToCountriesDatasetView.as_view(),
        name='company-export-to-countries-dataset',
    ),
    path(
        'company-future-interest-countries-dataset',
        CompanyFutureInterestCountriesDatasetView.as_view(),
        name='company-future-interest-countries-dataset',
    ),
    path('interactions-dataset', InteractionsDatasetView.as_view(), name='interactions-dataset'),
    path(
        'interactions-export-country-dataset',
        InteractionsExportCountryDatasetView.as_view(),
        name='interactions-export-country-dataset',
    ),
    path('teams-dataset', TeamsDatasetView.as_view(), name='teams-dataset'),
    path(
        'investment-projects-dataset',
        InvestmentProjectsDatasetView.as_view(),
        name='investment-projects-dataset',
    ),
    path(
        'investment-projects-activity-dataset',
        InvestmentProjectsActivityDatasetView.as_view(),
        name='investment-projects-activity-dataset',
    ),
    path('events-dataset', EventsDatasetView.as_view(), name='events-dataset'),
]
