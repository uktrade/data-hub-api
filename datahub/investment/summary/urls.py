from django.urls import path

from datahub.investment.summary.views import IProjectSummaryView


urlpatterns = [
    path(
        'adviser/<uuid:adviser_pk>/investment-summary',
        IProjectSummaryView.as_view(),
        name='investment-summary-item',
    ),
]
