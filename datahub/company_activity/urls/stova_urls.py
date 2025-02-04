from django.urls import path

from .. import views

urlpatterns = [
    path('<uuid:pk>', views.StovaEventRetrieveAPIView.as_view(), name='detail'),
]
