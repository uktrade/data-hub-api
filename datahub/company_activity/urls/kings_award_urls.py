from django.urls import path

from datahub.company_activity.views import KingsAwardRecipientViewSet

urlpatterns = [
    path('', KingsAwardRecipientViewSet.as_view({'get': 'list'}), name='collection'),
]
