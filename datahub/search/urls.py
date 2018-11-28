"""Search views URL config."""

from django.urls import path

from datahub.search.apps import get_search_apps
from datahub.search.views import SearchBasicAPIView


urlpatterns = [
    path('search', SearchBasicAPIView.as_view(), name='basic'),
]

for search_app in get_search_apps():
    if search_app.view:
        urlpatterns.append(path(
            f'search/{search_app.name}',
            search_app.view.as_view(search_app=search_app),
            name=search_app.name,
        ))

    if search_app.export_view:
        urlpatterns.append(path(
            f'search/{search_app.name}/export',
            search_app.export_view.as_view(search_app=search_app),
            name=f'{search_app.name}-export',
        ))

    if search_app.autocomplete_view:
        urlpatterns.append(path(
            f'search/{search_app.name}/autocomplete',
            search_app.autocomplete_view.as_view(search_app=search_app),
            name=f'{search_app.name}-autocomplete-search',
        ))
