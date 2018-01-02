from functools import partial

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .registry import registry


@api_view()
@authentication_classes([])
@permission_classes([])
def metadata_view(request, mapping):
    """Metadata generic view."""
    qs = mapping.queryset.all()
    serializer = mapping.serializer(qs, many=True)
    return Response(data=serializer.data)


urls_args = []

# programmatically generate metadata views
for name, mapping in registry.mappings.items():
    fn = partial(metadata_view, mapping=mapping)
    path = f'{name}/'
    urls_args.append(((path, fn), {'name': name}))
