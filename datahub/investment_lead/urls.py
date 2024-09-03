from django.urls import path

from datahub.investment_lead.views import EYBLeadViewset

urlpatterns = [
    path(
        'eyb',
        EYBLeadViewset.as_view({'post': 'create'}),
        name='eyb-create',
    ),
]
