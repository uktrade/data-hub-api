from django.urls import path

from datahub.activity_stream.views import ActivityStreamViewSet

activity_stream_urls = [
    path(
        'activity-stream/',
        ActivityStreamViewSet.as_view({'get': 'list'}),
        name='index'
    ),
]
