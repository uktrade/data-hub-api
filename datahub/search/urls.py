"""Search views URL config."""

from django.urls import path

from datahub.search.apps import get_search_apps
from datahub.search.views import SearchBasicAPIView


def _construct_path(search_app, view, suffix=None):
    if not view:
        return []

    url = f'search/{search_app.name}'
    if suffix:
        url = f'{url}/{suffix}'

    url_name = search_app.name
    if suffix:
        url_name = f'{url_name}-{suffix}'

    return [
        path(
            url,
            view.as_view(search_app=search_app),
            name=url_name,
        ),
    ]


# API V3

urls_v3 = [
    path('search', SearchBasicAPIView.as_view(), name='basic'),
]

for search_app in get_search_apps():
    urls_v3.extend(
        [
            *_construct_path(search_app, search_app.view),
            *_construct_path(
                search_app,
                search_app.export_view,
                'export',
            ),
            *_construct_path(
                search_app,
                search_app.autocomplete_view,
                'autocomplete',
            ),
        ],
    )


# API V4 - new format for addresses

# TODO add global search when all search apps are v4 ready
urls_v4 = []

for search_app in get_search_apps():
    urls_v4.extend(
        [
            *_construct_path(search_app, search_app.view_v4),
            *_construct_path(
                search_app,
                search_app.export_view_v4,
                'export',
            ),
            *_construct_path(
                search_app,
                search_app.autocomplete_view_v4,
                'autocomplete',
            ),
        ],
    )
