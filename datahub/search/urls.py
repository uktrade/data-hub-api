"""Search views URL config."""

from django.conf.urls import url

from .apps import get_search_apps
from .views import SearchBasicAPIView

urlpatterns = [
    url(r'^search$', SearchBasicAPIView.as_view(), name='basic'),
]

for search_app in get_search_apps():
    urlpatterns.append(
        url(rf'^search/{search_app.name}$', search_app.view.as_view(), name=search_app.name),
    )
