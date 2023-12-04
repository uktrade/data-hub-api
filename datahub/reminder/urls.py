from django.urls import path

from datahub.reminder.views import (
    NewExportInteractionReminderViewset,
    NewExportInteractionSubscriptionViewset,
    NoRecentExportInteractionReminderViewset,
    NoRecentExportInteractionSubscriptionViewset,
    NoRecentInvestmentInteractionReminderViewset,
    NoRecentInvestmentInteractionSubscriptionViewset,
    reminder_subscription_summary_view,
    reminder_summary_view,
    TaskAmendedByOthersSubscriptionViewset,
    TaskAmendedByOthersReminderViewset,
    TaskAssignedToMeFromOthersReminderViewset,
    TaskAssignedToMeFromOthersSubscriptionViewset,
    TaskCompletedReminderViewset,
    TaskCompletedSubscriptionViewset,
    TaskOverdueReminderViewset,
    TaskOverdueSubscriptionViewset,
    UpcomingEstimatedLandDateReminderViewset,
    UpcomingEstimatedLandDateSubscriptionViewset,
    UpcomingTaskReminderSubscriptionViewset,
    UpcomingTaskReminderViewset,
)

urlpatterns = [
    path(
        'reminder/subscription/no-recent-export-interaction',
        NoRecentExportInteractionSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='no-recent-export-interaction-subscription',
    ),
    path(
        'reminder/subscription/new-export-interaction',
        NewExportInteractionSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='new-export-interaction-subscription',
    ),
    path(
        'reminder/subscription/no-recent-investment-interaction',
        NoRecentInvestmentInteractionSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='no-recent-investment-interaction-subscription',
    ),
    path(
        'reminder/subscription/estimated-land-date',
        UpcomingEstimatedLandDateSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='estimated-land-date-subscription',
    ),
    path(
        'reminder/subscription/summary',
        reminder_subscription_summary_view,
        name='subscription-summary',
    ),
    path(
        'reminder/new-export-interaction',
        NewExportInteractionReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='new-export-interaction-reminder',
    ),
    path(
        'reminder/new-export-interaction/<uuid:pk>',
        NewExportInteractionReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='new-export-interaction-reminder-detail',
    ),
    path(
        'reminder/no-recent-export-interaction',
        NoRecentExportInteractionReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='no-recent-export-interaction-reminder',
    ),
    path(
        'reminder/no-recent-export-interaction/<uuid:pk>',
        NoRecentExportInteractionReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='no-recent-export-interaction-reminder-detail',
    ),
    path(
        'reminder/no-recent-investment-interaction',
        NoRecentInvestmentInteractionReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='no-recent-investment-interaction-reminder',
    ),
    path(
        'reminder/no-recent-investment-interaction/<uuid:pk>',
        NoRecentInvestmentInteractionReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='no-recent-investment-interaction-reminder-detail',
    ),
    path(
        'reminder/estimated-land-date',
        UpcomingEstimatedLandDateReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='estimated-land-date-reminder',
    ),
    path(
        'reminder/estimated-land-date/<uuid:pk>',
        UpcomingEstimatedLandDateReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='estimated-land-date-reminder-detail',
    ),
    path(
        'reminder/my-tasks-due-date-approaching',
        UpcomingTaskReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='my-tasks-due-date-approaching-reminder',
    ),
    path(
        'reminder/my-tasks-due-date-approaching/<uuid:pk>',
        UpcomingTaskReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='my-tasks-due-date-approaching-reminder-detail',
    ),
    path(
        'reminder/subscription/my-tasks-due-date-approaching',
        UpcomingTaskReminderSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='my-tasks-due-date-approaching-subscription',
    ),
    path(
        'reminder/task-assigned-to-me-from-others',
        TaskAssignedToMeFromOthersReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='task-assigned-to-me-from-others-reminder',
    ),
    path(
        'reminder/task-assigned-to-me-from-others/<uuid:pk>',
        TaskAssignedToMeFromOthersReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='task-assigned-to-me-from-others-reminder-detail',
    ),
    path(
        'reminder/subscription/task-assigned-to-me-from-others',
        TaskAssignedToMeFromOthersSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='task-assigned-to-me-from-others-subscription',
    ),
    path(
        'reminder/my-tasks-task-overdue',
        TaskOverdueReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='my-tasks-task-overdue-reminder',
    ),
    path(
        'reminder/my-tasks-task-overdue/<uuid:pk>',
        TaskOverdueReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='my-tasks-task-overdue-reminder-detail',
    ),
    path(
        'reminder/subscription/my-tasks-task-overdue',
        TaskOverdueSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='my-tasks-task-overdue-subscription',
    ),
    path(
        'reminder/subscription/task-amended-by-others',
        TaskAmendedByOthersSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='task-amended-by-others-subscription',
    ),
    path(
        'reminder/my-tasks-task-amended-by-others',
        TaskAmendedByOthersReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='my-tasks-task-amended-by-others-reminder',
    ),
    path(
        'reminder/my-tasks-task-amended-by-others/<uuid:pk>',
        TaskAmendedByOthersReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='my-tasks-task-amended-by-others-reminder-detail',
    ),
    path(
        'reminder/my-tasks-task-completed',
        TaskCompletedReminderViewset.as_view(
            {
                'get': 'list',
            },
        ),
        name='my-tasks-task-completed-reminder',
    ),
    path(
        'reminder/my-tasks-task-completed/<uuid:pk>',
        TaskCompletedReminderViewset.as_view(
            {
                'delete': 'destroy',
            },
        ),
        name='my-tasks-task-completed-reminder-detail',
    ),
    path(
        'reminder/subscription/my-tasks-task-completed',
        TaskCompletedSubscriptionViewset.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='my-tasks-task-completed-subscription',
    ),
    path(
        'reminder/summary',
        reminder_summary_view,
        name='summary',
    ),
]
