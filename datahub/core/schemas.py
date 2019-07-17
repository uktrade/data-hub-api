import coreapi
from rest_framework import serializers
from rest_framework.schemas.coreapi import AutoSchema, field_to_schema


class ExplicitSerializerSchema(AutoSchema):
    """
    Subclass of AutoSchema that explicitly takes a serializer rather than using the one defined
    on the view set.

    This is useful for extra routes added to view sets.

    Note: This does not currently support ListSerializer.

    Usage example:

        from rest_framework.decorators import action

        class MyViewSet(CoreViewSet):
            @action(
                methods=['post'],
                detail=True,
                schema=ExplicitSerializerSchema(request_body_serializer=ArchiveSerializer()),
            )
            def archive(self, request, pk):
                pass


    See also: CoreViewSet.as_action_view
    """

    def __init__(
        self,
        query_string_serializer=None,
        request_body_serializer=None,
        *args,
        **kwargs,
    ):
        """Initialise the schema with query string and request body serialisers."""
        super().__init__(*args, **kwargs)

        self.query_string_serializer = query_string_serializer
        self.request_body_serializer = request_body_serializer

    def get_query_string_serializer(self):
        """Get an instance of the serializer used for the query string."""
        return self.query_string_serializer

    def get_request_body_serializer(self):
        """Get an instance of the serializer used for the request body."""
        return self.request_body_serializer

    def get_serializer_configs(self, method):
        """
        Get a list of (serializer instance, is_partial, location) tuples.

        See `get_fields_for_serializer` for the meaning of is_partial and location.
        """
        serializer_configs = []

        request_body_serializer = self.get_request_body_serializer()

        if request_body_serializer:
            serializer_configs.append((request_body_serializer, method == 'PATCH', 'form'))

        query_string_serializer = self.get_query_string_serializer()

        if query_string_serializer:
            serializer_configs.append((query_string_serializer, False, 'query'))

        return serializer_configs

    def get_serializer_fields(self, path, method):
        """Get schema fields for the serializers returned by get_serializer_configs()."""
        serializer_configs = self.get_serializer_configs(method)

        return [
            field
            for serializer, is_partial, location in serializer_configs
            for field in get_fields_for_serializer(serializer, is_partial, location)
        ]


def get_fields_for_serializer(serializer, is_partial, location):
    """
    Generate a list of schema fields for a serializer.

    :param serializer: a serializer instance
    :param is_partial: whether this is a partial update (e.g. a PATCH request)
    :param location: location of the generated fields
        (valid values include 'form' for the request body and 'query' for the query string)
    """
    writable_fields = (
        field for field in serializer.fields.values()
        if not (field.read_only or isinstance(field, serializers.HiddenField))
    )

    return [
        coreapi.Field(
            name=field.field_name,
            location=location,
            required=field.required and not is_partial,
            schema=field_to_schema(field),
        )
        for field in writable_fields
    ]
