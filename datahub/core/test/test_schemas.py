import coreapi
import coreschema
import pytest
from rest_framework import serializers

from datahub.core.schemas import ExplicitSerializerSchema


class SimpleSerializer(serializers.Serializer):
    """Example serializer used in the tests below."""

    field_a = serializers.CharField(required=False)
    field_b = serializers.IntegerField(required=True)


class TestExplicitSerializerSchema:
    """Tests for ExplicitSerializerSchema."""

    @pytest.mark.parametrize(
        'initkwargs,http_method,expected_fields',
        (
            pytest.param(
                {'request_body_serializer': SimpleSerializer()},
                'POST',
                [
                    coreapi.Field(
                        'field_a',
                        False,
                        'form',
                        coreschema.String(title='Field a', description=''),
                    ),
                    coreapi.Field(
                        'field_b',
                        True,
                        'form',
                        coreschema.Integer(title='Field b', description=''),
                    ),
                ],
                id='request body, POST',
            ),
            pytest.param(
                {'request_body_serializer': SimpleSerializer()},
                'PATCH',
                [
                    coreapi.Field(
                        'field_a',
                        False,
                        'form',
                        coreschema.String(title='Field a', description=''),
                    ),
                    coreapi.Field(
                        'field_b',
                        False,
                        'form',
                        coreschema.Integer(title='Field b', description=''),
                    ),
                ],
                id='request body, PATCH',
            ),
            pytest.param(
                {'query_string_serializer': SimpleSerializer()},
                'PATCH',
                [
                    coreapi.Field(
                        'field_a',
                        False,
                        'query',
                        coreschema.String(title='Field a', description=''),
                    ),
                    coreapi.Field(
                        'field_b',
                        True,
                        'query',
                        coreschema.Integer(title='Field b', description=''),
                    ),
                ],
                id='query string',
            ),
        ),
    )
    def test_get_serializer_fields(self, initkwargs, http_method, expected_fields):
        """Test get_serializer_fields()."""
        schema = ExplicitSerializerSchema(**initkwargs)
        assert schema.get_serializer_fields('/path', http_method) == expected_fields
