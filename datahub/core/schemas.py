import coreapi
from rest_framework import serializers
from rest_framework.schemas import AutoSchema
from rest_framework.schemas.inspectors import field_to_schema


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
                schema=ExplicitSerializerSchema(ArchiveSerializer),
            )
            def archive(self, request, pk):
                pass


    See also: CoreViewSet.as_action_view
    """

    def __init__(self, serializer_cls, *args, **kwargs):
        """Initialise the schema with a serialiser."""
        super().__init__(*args, **kwargs)

        self.serializer_cls = serializer_cls

    def get_serializer_fields(self, path, method):
        """
        Get the schema fields for self.serializer_cls.

        This logic is based on the equivalent logic in AutoSchema.
        """
        serializer = self.serializer_cls()
        is_partial = method == 'PATCH'

        writable_fields = (
            field for field in serializer.fields.values()
            if not (field.read_only or isinstance(field, serializers.HiddenField))
        )

        return [
            coreapi.Field(
                name=field.field_name,
                location='form',
                required=field.required and not is_partial,
                schema=field_to_schema(field),
            )
            for field in writable_fields
        ]
