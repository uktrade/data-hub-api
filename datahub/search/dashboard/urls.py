from django.urls import path

from datahub.search.dashboard.views import IntelligentHomepageView


urlpatterns = [
    path('homepage/', IntelligentHomepageView.as_view(), name='intelligent-homepage'),
]
