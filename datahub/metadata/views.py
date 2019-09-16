from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from config.settings.types import HawkScope
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.metadata.registry import registry


# TODO: remove function parameters once legacy views have been removed after deprecation period
def _create_metadata_view(mapping, view_set_types=None, auth_attributes=None):
    has_filters = mapping.filterset_fields or mapping.filterset_class
    model = mapping.queryset.model

    attrs = {
        'filter_backends': (DjangoFilterBackend,) if has_filters else (),
        'filterset_class': mapping.filterset_class,
        'filterset_fields': mapping.filterset_fields,
        'pagination_class': None,
        'queryset': mapping.queryset,
        'serializer_class': mapping.serializer,
        '__doc__': f'List all {model._meta.verbose_name_plural}.',
    }
    attrs.update(auth_attributes or _get_hawk_auth_attributes())

    view_set = type(
        f'{mapping.model.__name__}ViewSet',
        view_set_types or (HawkResponseSigningMixin, GenericViewSet, ListModelMixin),
        attrs,
    )

    return view_set.as_view({
        'get': 'list',
    })


def _get_hawk_auth_attributes():
    return {
        'authentication_classes': (HawkAuthentication, ),
        'permission_classes': (HawkScopePermission, ),
        'required_hawk_scope': HawkScope.metadata,
    }


# TODO: this function needs be removed after a deprecation period
def _get_public_access_auth_attributes():
    return {
        'authentication_classes': (),
        'permission_classes': (),
    }


urls_args = []

# programmatically generate metadata views
for name, mapping in registry.mappings.items():
    view = _create_metadata_view(mapping)
    urls_args.append(((name, view), {'name': name}))


# TODO: views below need to be removed after deprecation period is over
legacy_urls_args = []

for name, mapping in registry.mappings.items():
    view = _create_metadata_view(
        mapping,
        (GenericViewSet, ListModelMixin),
        _get_public_access_auth_attributes(),
    )
    path = f'{name}/'
    legacy_urls_args.append(((path, view), {'name': name}))
