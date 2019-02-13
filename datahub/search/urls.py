"""Search views URL config."""

from django.urls import path

from datahub.search.apps import get_search_apps
from datahub.search.views import SearchBasicAPIView

# API V3

urls_v3 = [
    path('search', SearchBasicAPIView.as_view(), name='basic'),
]

for search_app in get_search_apps():
    if search_app.view:
        urls_v3.append(path(
            f'search/{search_app.name}',
            search_app.view.as_view(search_app=search_app),
            name=search_app.name,
        ))

    if search_app.export_view:
        urls_v3.append(path(
            f'search/{search_app.name}/export',
            search_app.export_view.as_view(search_app=search_app),
            name=f'{search_app.name}-export',
        ))

    if search_app.autocomplete_view:
        urls_v3.append(path(
            f'search/{search_app.name}/autocomplete',
            search_app.autocomplete_view.as_view(search_app=search_app),
            name=f'{search_app.name}-autocomplete-search',
        ))


# API V4 - new format for addresses

# TODO add global search when all search apps are v4 ready
urls_v4 = []

for search_app in get_search_apps():
    if search_app.view_v4:
        urls_v4.append(path(
            f'search/{search_app.name}',
            search_app.view_v4.as_view(search_app=search_app),
            name=search_app.name,
        ))

    if search_app.export_view_v4:
        urls_v4.append(path(
            f'search/{search_app.name}/export',
            search_app.export_view_v4.as_view(search_app=search_app),
            name=f'{search_app.name}-export',
        ))

    if search_app.autocomplete_view_v4:
        urls_v4.append(path(
            f'search/{search_app.name}/autocomplete',
            search_app.autocomplete_view_v4.as_view(search_app=search_app),
            name=f'{search_app.name}-autocomplete-search',
        ))
