from django.urls import path

from datahub.activity_stream.interaction.views import InteractionActivityViewSet
from datahub.activity_stream.investment.views import IProjectCreatedViewSet

activity_stream_urls = [
    path(
        'activity-stream/interaction',
        InteractionActivityViewSet.as_view({'get': 'list'}),
        name='interactions',
    ),
    path(
        'activity-stream/investment/project-added',
        IProjectCreatedViewSet.as_view({'get': 'list'}),
        name='investment-project-added',
    ),
]
