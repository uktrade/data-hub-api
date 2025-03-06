from datetime import datetime

import pytest

from django.contrib.contenttypes.models import ContentType

from datahub.documents.models import GenericDocument
from datahub.documents.utils import format_content_type


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


pytestmark = pytest.mark.django_db


def test_format_content_type():
    content_type = ContentType.objects.get_for_model(GenericDocument)
    result = format_content_type(content_type)
    expected = f'{content_type.app_label}.{content_type.model}'
    assert result == expected


def assert_retrieved_sharepoint_document(instance, retrieved_instance):
    """Asserts retrieved JSON contains the correct fields and data from the SharePointDocument."""
    assert str(instance.id) == retrieved_instance['id']

    assert str(instance.created_by.id) == retrieved_instance['created_by']['id']
    assert str(instance.modified_by.id) == retrieved_instance['modified_by']['id']

    assert instance.created_on.timestamp() == \
        datetime.strptime(retrieved_instance['created_on'], DATETIME_FORMAT).timestamp()
    assert instance.modified_on.timestamp() == \
        datetime.strptime(retrieved_instance['modified_on'], DATETIME_FORMAT).timestamp()

    assert instance.archived == retrieved_instance['archived']
    assert instance.archived_on == retrieved_instance['archived_on']
    assert instance.archived_reason == retrieved_instance['archived_reason']

    assert instance.title == retrieved_instance['title']
    assert instance.url == retrieved_instance['url']


def assert_retrieved_generic_document(instance, retrieved_instance):
    """Asserts retrieved JSON contains the correct fields and data from the GenericDocument."""
    assert str(instance.id) == retrieved_instance['id']

    assert str(instance.created_by.id) == retrieved_instance['created_by']['id']
    assert str(instance.modified_by.id) == retrieved_instance['modified_by']['id']

    assert instance.created_on.timestamp() == \
        datetime.strptime(retrieved_instance['created_on'], DATETIME_FORMAT).timestamp()
    assert instance.modified_on.timestamp() == \
        datetime.strptime(retrieved_instance['modified_on'], DATETIME_FORMAT).timestamp()

    assert instance.archived == retrieved_instance['archived']
    assert instance.archived_on == retrieved_instance['archived_on']
    assert instance.archived_reason == retrieved_instance['archived_reason']

    assert str(instance.document.id) == retrieved_instance['document']['id']
    assert str(instance.related_object.id) == retrieved_instance['related_object']['id']
    assert str(instance.document_object_id) == retrieved_instance['document_object_id']
    assert str(instance.related_object_id) == retrieved_instance['related_object_id']

    assert format_content_type(instance.document_type) == retrieved_instance['document_type']
    assert format_content_type(instance.related_object_type) == \
        retrieved_instance['related_object_type']
