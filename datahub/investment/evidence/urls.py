"""Investment project evidence group views URL config."""

from django.urls import path

from datahub.investment.evidence.views import EvidenceGroupViewSet

evidence_group_collection = EvidenceGroupViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

evidence_group_item = EvidenceGroupViewSet.as_view({
    'get': 'retrieve',
})


urlpatterns = [
    path('evidence-group', evidence_group_collection, name='collection'),
    path('evidence-group/<uuid:evidence_group_pk>', evidence_group_item, name='item'),
]
