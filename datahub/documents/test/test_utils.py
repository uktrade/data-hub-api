import pytest

from django.contrib.contenttypes.models import ContentType

from datahub.documents.models import GenericDocument
from datahub.documents.utils import format_content_type


pytestmark = pytest.mark.django_db


def test_format_content_type():
    content_type = ContentType.objects.get_for_model(GenericDocument)
    result = format_content_type(content_type)
    expected = f'{content_type.app_label}.{content_type.model}'
    assert result == expected
