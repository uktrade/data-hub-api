from django.urls import path

from datahub.activity_feed.views import ActivityFeedView

urlpatterns = [
    path(
        'activity-feed',
        ActivityFeedView.as_view(),
        name='index',
    ),
]
