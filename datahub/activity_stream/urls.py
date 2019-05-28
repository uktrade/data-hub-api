from django.urls import path

from datahub.activity_stream.interaction.views import InteractionActivityViewSet

activity_stream_urls = [
    path(
        'activity-stream/interactions',
        InteractionActivityViewSet.as_view({'get': 'list'}),
        name='interactions',
    ),
]
