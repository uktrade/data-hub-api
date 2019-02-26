"""Search views URL config."""

from django.urls import path

from datahub.search.views import SearchBasicAPIView, v3_view_registry, v4_view_registry


def _construct_path(search_app, view, suffix=None):
    url = f'search/{search_app.name}'
    if suffix:
        url = f'{url}/{suffix}'

    url_name = search_app.name
    if suffix:
        url_name = f'{url_name}-{suffix}'

    return path(
        url,
        view.as_view(search_app=search_app),
        name=url_name,
    )


# API V3

urls_v3 = [
    path('search', SearchBasicAPIView.as_view(), name='basic'),
    *[
        _construct_path(search_app, view_cls, suffix=name)
        for (search_app, name), view_cls in v3_view_registry.items()
    ],
]


# API V4 - new format for addresses

# TODO add global search when all search apps are v4 ready
urls_v4 = [
    _construct_path(search_app, view_cls, suffix=name)
    for (search_app, name), view_cls in v4_view_registry.items()
]
