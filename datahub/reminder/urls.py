from django.urls import path

from datahub.reminder.views import (
    NoRecentInvestmentInteractionReminderViewset,
    NoRecentInvestmentInteractionSubscriptionViewset,
    UpcomingEstimatedLandDateReminderViewset,
    UpcomingEstimatedLandDateSubscriptionViewset,
)


urlpatterns = [
    path(
        'reminder/subscription/no-recent-investment-interaction',
        NoRecentInvestmentInteractionSubscriptionViewset.as_view({
            'get': 'retrieve',
        }),
        name='no-recent-investment-interaction-subscription',
    ),
    path(
        'reminder/subscription/estimated-land-date',
        UpcomingEstimatedLandDateSubscriptionViewset.as_view({
            'get': 'retrieve',
        }),
        name='estimated-land-date-subscription',
    ),

    path(
        'reminder/no-recent-investment-interaction',
        NoRecentInvestmentInteractionReminderViewset.as_view({
            'get': 'list',
        }),
        name='no-recent-investment-interaction-reminder',
    ),
    path(
        'reminder/estimated-land-date',
        UpcomingEstimatedLandDateReminderViewset.as_view({
            'get': 'list',
        }),
        name='estimated-land-date-reminder',
    ),
]
