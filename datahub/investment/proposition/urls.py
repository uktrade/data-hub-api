"""Investment project proposition views URL config."""

from django.urls import path

from datahub.investment.proposition.views import PropositionViewSet

proposition_collection = PropositionViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

proposition_item = PropositionViewSet.as_view({
    'get': 'retrieve',
})

proposition_complete = PropositionViewSet.as_view({
    'post': 'complete',
})

proposition_abandon = PropositionViewSet.as_view({
    'post': 'abandon',
})

urlpatterns = [
    path('proposition', proposition_collection, name='collection'),
    path('proposition/<uuid:pk>', proposition_item, name='item'),
    path('proposition/<uuid:pk>/complete', proposition_complete, name='complete'),
    path('proposition/<uuid:pk>/abandon', proposition_abandon, name='abandon'),
]
