from django.urls import path

from datahub.dataset.adviser.views import AdvisersDatasetView
from datahub.dataset.company.views import CompaniesDatasetView
from datahub.dataset.company_export.views import CompanyExportDatasetView
from datahub.dataset.company_export_country.views import (
    CompanyExportCountryDatasetView,
)
from datahub.dataset.company_export_country_history.views import (
    CompanyExportCountryHistoryDatasetView,
)
from datahub.dataset.company_list.views import PipelineItemsDatasetView
from datahub.dataset.company_objective.views import (
    CompanyObjectiveDatasetView,
)
from datahub.dataset.company_referral.views import CompanyReferralDatasetView
from datahub.dataset.contact.views import ContactsDatasetView
from datahub.dataset.event.views import EventsDatasetView
from datahub.dataset.export_wins.views import (
    ExportWinsAdvisersDatasetView,
    ExportWinsBreakdownsDatasetView,
    ExportWinsHVCDatasetView,
    ExportWinsWinDatasetView,
)
from datahub.dataset.interaction.views import InteractionsDatasetView
from datahub.dataset.interaction_export_country.views import InteractionsExportCountryDatasetView
from datahub.dataset.investment_project.views import (
    InvestmentProjectsActivityDatasetView,
    InvestmentProjectsDatasetView,
)
from datahub.dataset.order.views import OMISDatasetView
from datahub.dataset.task.views import TasksDatasetView
from datahub.dataset.team.views import TeamsDatasetView
from datahub.dataset.user_event_log.views import UserEventsView


urlpatterns = [
    path('advisers-dataset', AdvisersDatasetView.as_view(), name='advisers-dataset'),
    path('omis-dataset', OMISDatasetView.as_view(), name='omis-dataset'),
    path('contacts-dataset', ContactsDatasetView.as_view(), name='contacts-dataset'),
    path('companies-dataset', CompaniesDatasetView.as_view(), name='companies-dataset'),
    path(
        'company-export-dataset',
        CompanyExportDatasetView.as_view(),
        name='company-export-dataset',
    ),
    path(
        'company-export-country-dataset',
        CompanyExportCountryDatasetView.as_view(),
        name='company-export-country-dataset',
    ),
    path(
        'company-export-country-history-dataset',
        CompanyExportCountryHistoryDatasetView.as_view(),
        name='company-export-country-history-dataset',
    ),
    path('interactions-dataset', InteractionsDatasetView.as_view(), name='interactions-dataset'),
    path(
        'interactions-export-country-dataset',
        InteractionsExportCountryDatasetView.as_view(),
        name='interactions-export-country-dataset',
    ),
    path('tasks-dataset', TasksDatasetView.as_view(), name='tasks-dataset'),
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
    path(
        'company-referrals-dataset',
        CompanyReferralDatasetView.as_view(),
        name='company-referrals-dataset',
    ),
    path(
        'pipeline-items-dataset',
        PipelineItemsDatasetView.as_view(),
        name='pipeline-items-dataset',
    ),
    path(
        'user-events-dataset',
        UserEventsView.as_view(),
        name='user-events-dataset',
    ),
    path(
        'company-objective-dataset',
        CompanyObjectiveDatasetView.as_view(),
        name='company-objective-dataset',
    ),
    path(
        'export-wins-advisers-dataset',
        ExportWinsAdvisersDatasetView.as_view(),
        name='export-wins-advisers-dataset',
    ),
    path(
        'export-wins-breakdowns-dataset',
        ExportWinsBreakdownsDatasetView.as_view(),
        name='export-wins-breakdowns-dataset',
    ),
    path(
        'export-wins-hvc-dataset',
        ExportWinsHVCDatasetView.as_view(),
        name='export-wins-hvc-dataset',
    ),
    path(
        'export-wins-win-dataset',
        ExportWinsWinDatasetView.as_view(),
        name='export-wins-win-dataset',
    ),
]
