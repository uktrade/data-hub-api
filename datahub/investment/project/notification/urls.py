"""Investment notification subscription views URL config."""

from django.urls import path

from datahub.investment.project.notification.views import (
    get_or_update_notification_subscription,
)

urlpatterns = [
    path(
        'notification',
        get_or_update_notification_subscription,
        name='notification-subscription',
    ),
]
