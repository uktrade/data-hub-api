from rest_framework import parsers
from rest_framework.exceptions import ParseError
from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.utils import format_keys

from .renderers import JSONRenderer


class JSONParser(parsers.JSONParser):
    """
    A JSON API client will send a payload that looks like this:

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

    @staticmethod
    def parse_attributes(data):
        if 'attributes' in data:
            return format_keys(data.get('attributes'), 'underscore')
        else:
            return dict()

    @staticmethod
    def parse_relationships(data):
        if 'relationships' in data:
            relationships = format_keys(data.get('relationships'), 'underscore')
        else:
            return dict()

        # Parse the relationships
        parsed_relationships = dict()
        for field_name, field_data in relationships.items():
            field_data = field_data.get('data')
            if isinstance(field_data, dict) or field_data is None:
                parsed_relationships[field_name] = field_data
            elif isinstance(field_data, list):
                parsed_relationships[field_name] = list(relation for relation in field_data)
        return parsed_relationships

    @staticmethod
    def parse_metadata(result):
        metadata = result.get('meta')
        if metadata:
            return {'_meta': metadata}
        else:
            return {}

    def parse(self, stream, media_type=None, parser_context=None):
        """Parse the incoming bytestream as JSON and returns the resulting data."""
        result = super(JSONParser, self).parse(
            stream, media_type=media_type, parser_context=parser_context)

        if not isinstance(result, dict) or 'data' not in result:
            raise ParseError('Received document does not contain primary data')

        data = result.get('data')

        request = parser_context.get('request')

        # Check for inconsistencies
        resource_name = parser_context['view'].entity_name
        if data.get('type') != resource_name and request.method in ('PUT', 'POST', 'PATCH'):
            raise Conflict(
                "The resource object's type ({data_type}) is not the type "
                "that constitute the collection represented by the endpoint ({resource_type}).".format(
                    data_type=data.get('type'),
                    resource_type=resource_name
                )
            )
        if not data.get('id') and request.method in ('PATCH', 'PUT'):
            raise ParseError("The resource identifier object must contain an 'id' member")
        return data
