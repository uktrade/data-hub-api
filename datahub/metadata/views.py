import logging
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from config.settings.types import HawkScope
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.metadata.registry import registry

logger = logging.getLogger(__name__)


class DBTPlatformFix:
    def dispatch(self, request, *args, **kwargs):
        logger.info("DISPATCH!!!!!!!!!!")
        logger.info(request)
        # if len(request.GET) == 0:
        request.GET._mutable = True
        request.GET['level__lte'] = 0
        return super().dispatch(request, *args, **kwargs)


def _create_metadata_view(mapping):
    has_filters = mapping.filterset_fields or mapping.filterset_class
    model = mapping.queryset.model
    attrs = {
        'dispatch': (DBTPlatformFix,),
        'authentication_classes': (PaaSIPAuthentication, HawkAuthentication),
        'permission_classes': (HawkScopePermission,),
        'required_hawk_scope': HawkScope.metadata,
        'filter_backends': (DjangoFilterBackend,) if has_filters else (),
        'filterset_class': mapping.filterset_class,
        'filterset_fields': mapping.filterset_fields,
        'pagination_class': None,
        'queryset': mapping.queryset,
        'serializer_class': mapping.serializer,
        '__doc__': f'List all {model._meta.verbose_name_plural}.',
    }

    view_set = type(
        f'{mapping.model.__name__}ViewSet',
        (DBTPlatformFix, HawkResponseSigningMixin, GenericViewSet, ListModelMixin),
        attrs,
    )

    return view_set.as_view({
        'get': 'list',
    })


urls_args = []

# programmatically generate metadata views
for name, mapping in registry.mappings.items():
    view = _create_metadata_view(mapping)
    urls_args.append(((name, view), {'name': name}))
