from django.urls import path

from datahub.investment_lead.views import EYBLeadViewset

urlpatterns = [
    path(
        'investment-lead',
        EYBLeadViewset.as_view({'post': 'create'}),
        name='create',
    ),
]
