from django.urls import path

from datahub.company_activity import views

urlpatterns = [
    path('<uuid:pk>', views.StovaEventRetrieveAPIView.as_view(), name='detail'),
]
