from drf_spectacular.openapi import AutoSchema


class StubSchema(AutoSchema):
    """Simple OpenAPI schema without request or response details.

    This can be used for extra view methods added to CoreViewSet to suppress the default
    request and response schema generation but still have the endpoints listed in the
    documentation.
    """

    def get_operation(self, path, path_regex, path_prefix, method, registry):
        """Get the operation schema.

        This takes the operationId and parameters that drf-spectacular generate,
        but discards request and response schemas.
        """
        default_schema = super().get_operation(
            path=path,
            path_regex=path_regex,
            path_prefix=path_prefix,
            method=method,
            registry=registry,
        )
        return {
            'operationId': default_schema.get('operationId', ''),
            'parameters': default_schema.get('parameters', []),
            'description': default_schema.get('description', ''),
        }
