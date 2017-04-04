"""Json api parser."""

from rest_framework import parsers
from rest_framework.exceptions import ParseError
from rest_framework_json_api.exceptions import Conflict

from .renderers import JSONRenderer


class JSONParser(parsers.JSONParser):
    """
    A JSON API client will send a payload that looks like this.

        {
            "data": {
                "type": "identities",
                "id": 1,
                "attributes": {
                    "first_name": "John",
                    "last_name": "Coltrane"
                }
            }
        }

    We extract the attributes so that DRF serializers can work as normal.
    """

    media_type = 'application/vnd.api+json'
    renderer_class = JSONRenderer

    def parse(self, stream, media_type=None, parser_context=None):
        """Parse the incoming bytestream as JSON and returns the resulting data."""
        result = super().parse(
            stream, media_type=media_type, parser_context=parser_context)

        if not isinstance(result, dict) or 'data' not in result:
            raise ParseError('Received document does not contain primary data.')

        data = result.get('data')
        request = parser_context.get('request')

        # Check for inconsistencies
        resource_name = parser_context['view'].entity_name
        if data.get('type') != resource_name and request.method in ('PUT', 'POST', 'PATCH'):
            raise Conflict(
                'The resource object\'s type ({data_type}) is not the type '
                'that constitute the collection represented by the endpoint ({resource_type}).'.format(
                    data_type=data.get('type'),
                    resource_type=resource_name
                )
            )
        return data
