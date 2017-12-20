"""Search views URL config."""

from django.conf.urls import url

from .apps import get_search_apps
from .views import SearchBasicAPIView

urlpatterns = [
    url(r'^search$', SearchBasicAPIView.as_view(), name='basic'),
]

for search_app in get_search_apps():
    if search_app.view:
        urlpatterns.append(url(
            rf'^search/{search_app.name}$',
            search_app.view.as_view(search_app=search_app),
            name=search_app.name
        ))

    if search_app.export_view:
        urlpatterns.append(url(
            rf'^search/{search_app.name}/export$',
            search_app.export_view.as_view(search_app=search_app),
            name=f'{search_app.name}-export'
        ))
