from collections import namedtuple

from django.core.exceptions import ImproperlyConfigured

from datahub.core.serializers import ConstantModelSerializer

MetadataMapping = namedtuple(
    'MetadataMapping',
    ['model', 'queryset', 'serializer', 'filterset_fields', 'filterset_class'],
)


class MetadataRegistry:
    """
    Registry for all metadata.

    To register a new metadata from your specific django app, create a new module
    called `metadata.py` and add these lines:

    >>> from datahub.metadata.registry import registry

    >>> registry.register(
            metadata_id=<metadata-id>,
            model=<model>,
            queryset=<queryset>,
            serializer=<serializer>
            path_prefix=<string>
        )

    Where:
        - metadata_id: id of the metadata
        - model: metadata model
        - queryset (optional): if you want to override the default one
        - serializer (optional): if you want to override the default one
        - path_prefix (optional): if you want to prefix the url path

    The data registered is currently used by metadata.views to generate views automatically.
    """

    def __init__(self):
        """Keeps a local copy of the metadata registered."""
        self.metadata = {}

    def register(
        self,
        metadata_id,
        model,
        queryset=None,
        serializer=ConstantModelSerializer,
        filterset_fields=None,
        filterset_class=None,
        path_prefix=None,
    ):
        """Registers a new metadata."""
        if path_prefix:
            metadata_id = f'{path_prefix}/{metadata_id}'

        if metadata_id in self.metadata:
            raise ImproperlyConfigured(f'Metadata {metadata_id} already registered.')

        queryset = queryset if queryset is not None else model.objects.all()
        self.metadata[metadata_id] = MetadataMapping(
            model,
            queryset,
            serializer,
            filterset_fields,
            filterset_class,
        )

    @property
    def mappings(self):
        """Returns the metadata mappings as a dict."""
        return self.metadata


registry = MetadataRegistry()
