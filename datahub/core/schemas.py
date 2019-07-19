from rest_framework.schemas.openapi import AutoSchema


class StubSchema(AutoSchema):
    """
    Simple OpenAPI schema without request or response details.

    This can be used for extra view methods added to CoreViewSet to suppress the default
    request and response schema generation but still have the endpoints listed in the
    documentation.
    """

    def get_operation(self, path, method):
        """
        Get the operation schema.

        This takes the operationId and parameters that DRF generate, but discards request and
        response schemas.
        """
        default_schema = super().get_operation(path, method)
        return {
            'operationId': default_schema['operationId'],
            'parameters': default_schema['parameters'],
        }
