from django.urls import path

from datahub.investment_lead.views import (
    EYBLeadCreateView
)

urlpatterns = [
    path(
        'eyb-lead-create',
        EYBLeadCreateView.as_view(),
        name='eyb-lead-create',
    ),
]
