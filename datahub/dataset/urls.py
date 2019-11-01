from django.urls import path

from datahub.dataset.adviser.views import AdvisersDatasetView
from datahub.dataset.company.views import CompaniesDatasetView
from datahub.dataset.contact.views import ContactsDatasetView
from datahub.dataset.event.views import EventsDatasetView
from datahub.dataset.interaction.views import InteractionsDatasetView
from datahub.dataset.investment_project.views import InvestmentProjectsDatasetView
from datahub.dataset.order.views import OMISDatasetView
from datahub.dataset.team.views import TeamsDatasetView


urlpatterns = [
    path('advisers-dataset', AdvisersDatasetView.as_view(), name='advisers-dataset'),
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
    path('contacts-dataset', ContactsDatasetView.as_view(), name='contacts-dataset'),
    path('companies-dataset', CompaniesDatasetView.as_view(), name='companies-dataset'),
    path('interactions-dataset', InteractionsDatasetView.as_view(), name='interactions-dataset'),
    path('teams-dataset', TeamsDatasetView.as_view(), name='teams-dataset'),
    path(
        'investment-projects-dataset',
        InvestmentProjectsDatasetView.as_view(),
        name='investment-projects-dataset',
    ),
    path('events-dataset', EventsDatasetView.as_view(), name='events-dataset'),
]
