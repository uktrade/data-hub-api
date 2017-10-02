from functools import partial

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from datahub.core.models import DisableableModel
from .registry import registry
from .serializers import DisableableRequestSerializer


@api_view()
@authentication_classes([])
@permission_classes([])
def metadata_view(request, mapping):
    """Metadata generic view."""
    qs = mapping.queryset.all()

    if issubclass(mapping.model, DisableableModel):
        validated_request = DisableableRequestSerializer(data=request.query_params)
        validated_request.is_valid(raise_exception=True)
        is_disabled = validated_request.validated_data.get('is_disabled')
        if is_disabled is not None:
            qs = qs.filter(disabled_on__isnull=(not is_disabled))

    serializer = mapping.serializer(qs, many=True)
    return Response(data=serializer.data)


urls_args = []

# programmatically generate metadata views
for name, mapping in registry.mappings.items():
    fn = partial(metadata_view, mapping=mapping)
    path = fr'^{name}/$'
    urls_args.append(((path, fn), {'name': name}))
