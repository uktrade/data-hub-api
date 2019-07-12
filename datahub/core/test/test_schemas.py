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
        'http_method,expected_fields',
        (
            pytest.param(
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
            ),
            pytest.param(
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
            ),
        ),
    )
    def test_get_serializer_fields(self, http_method, expected_fields):
        """Test get_serializer_fields()."""
        schema = ExplicitSerializerSchema(request_body_serializer=SimpleSerializer())
        assert schema.get_serializer_fields('/path', http_method) == expected_fields
