from django.urls import path

from datahub.reminder.views import (
    NoRecentInvestmentInteractionSubscriptionViewset,
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
]
