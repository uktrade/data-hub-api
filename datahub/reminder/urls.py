from django.urls import path

from datahub.reminder.views import (
    NewExportInteractionSubscriptionViewset,
    NoRecentExportInteractionReminderViewset,
    NoRecentExportInteractionSubscriptionViewset,
    NoRecentInvestmentInteractionReminderViewset,
    NoRecentInvestmentInteractionSubscriptionViewset,
    reminder_subscription_summary_view,
    reminder_summary_view,
    UpcomingEstimatedLandDateReminderViewset,
    UpcomingEstimatedLandDateSubscriptionViewset,
)

urlpatterns = [
    path(
        'reminder/subscription/no-recent-export-interaction',
        NoRecentExportInteractionSubscriptionViewset.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
        }),
        name='no-recent-export-interaction-subscription',
    ),
    path(
        'reminder/subscription/new-export-interaction',
        NewExportInteractionSubscriptionViewset.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
        }),
        name='new-export-interaction-subscription',
    ),
    path(
        'reminder/subscription/no-recent-investment-interaction',
        NoRecentInvestmentInteractionSubscriptionViewset.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
        }),
        name='no-recent-investment-interaction-subscription',
    ),
    path(
        'reminder/subscription/estimated-land-date',
        UpcomingEstimatedLandDateSubscriptionViewset.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
        }),
        name='estimated-land-date-subscription',
    ),
    path(
        'reminder/subscription/summary',
        reminder_subscription_summary_view,
        name='subscription-summary',
    ),

    path(
        'reminder/no-recent-export-interaction',
        NoRecentExportInteractionReminderViewset.as_view({
            'get': 'list',
        }),
        name='no-recent-export-interaction-reminder',
    ),
    path(
        'reminder/no-recent-export-interaction/<uuid:pk>',
        NoRecentExportInteractionReminderViewset.as_view({
            'delete': 'destroy',
        }),
        name='no-recent-export-interaction-reminder-detail',
    ),
    path(
        'reminder/no-recent-investment-interaction',
        NoRecentInvestmentInteractionReminderViewset.as_view({
            'get': 'list',
        }),
        name='no-recent-investment-interaction-reminder',
    ),
    path(
        'reminder/no-recent-investment-interaction/<uuid:pk>',
        NoRecentInvestmentInteractionReminderViewset.as_view({
            'delete': 'destroy',
        }),
        name='no-recent-investment-interaction-reminder-detail',
    ),
    path(
        'reminder/estimated-land-date',
        UpcomingEstimatedLandDateReminderViewset.as_view({
            'get': 'list',
        }),
        name='estimated-land-date-reminder',
    ),
    path(
        'reminder/estimated-land-date/<uuid:pk>',
        UpcomingEstimatedLandDateReminderViewset.as_view({
            'delete': 'destroy',
        }),
        name='estimated-land-date-reminder-detail',
    ),
    path(
        'reminder/summary',
        reminder_summary_view,
        name='summary',
    ),
]
