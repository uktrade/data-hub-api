"""Search views URL config."""

from django.urls import path

from datahub.core.utils import join_truthy_strings
from datahub.search.views import SearchBasicAPIView, v3_view_registry, v4_view_registry, ViewType


def _construct_path(search_app, view_type, view_cls, suffix=None):
    prefix = 'public' if view_type == ViewType.public else None

    url_parts = [
        prefix,
        'search',
        search_app.name,
        suffix,
    ]

    url = join_truthy_strings(*url_parts, sep='/')
    url_name = join_truthy_strings(prefix, search_app.name, suffix, sep='-')
    view = view_cls.as_view(search_app=search_app)

    return path(url, view, name=url_name)


# API V3

urls_v3 = [
    path('search', SearchBasicAPIView.as_view(), name='basic'),
    *[
        _construct_path(search_app, view_type, view_cls, suffix=name)
        for (search_app, view_type, name), view_cls in v3_view_registry.items()
    ],
]


# API V4 - new format for addresses

# TODO add global search when all search apps are v4 ready
urls_v4 = [
    _construct_path(search_app, view_type, view_cls, suffix=name)
    for (search_app, view_type, name), view_cls in v4_view_registry.items()
]
