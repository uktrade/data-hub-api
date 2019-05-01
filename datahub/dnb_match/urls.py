from django.urls import path

from datahub.dnb_match.views import (
    MatchingInformationAPIView,
    SelectMatchAPIView,
    SelectNoMatchAPIView,
)

urlpatterns = [
    path('<uuid:company_pk>', MatchingInformationAPIView.as_view(), name='item'),
    path('<uuid:company_pk>/select-match', SelectMatchAPIView.as_view(), name='select-match'),
    path(
        '<uuid:company_pk>/select-no-match',
        SelectNoMatchAPIView.as_view(),
        name='select-no-match',
    ),
]
