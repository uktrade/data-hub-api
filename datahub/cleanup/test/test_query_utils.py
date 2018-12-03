from unittest.mock import Mock

import pytest
from django.db.models import Q

from datahub.cleanup.query_utils import get_unreferenced_objects_query
from datahub.core.test.support.factories import BookFactory, PersonFactory
from datahub.core.test.support.models import Person


@pytest.mark.django_db
class TestGetUnreferencedObjectsQuery:
    """Tests get_unreferenced_objects_query()."""

    def test_raises_value_error_on_invalid_relation_exclusion_filter_mapping(self):
        """
        Test that ValueError is raised if relation_exclusion_filter_mapping contains invalid keys.
        """
        relation_exclusion_filter_mapping = {
            Mock(): Mock(),
        }
        with pytest.raises(ValueError):
            get_unreferenced_objects_query(
                Person,
                relation_exclusion_filter_mapping=relation_exclusion_filter_mapping,
            )

    def test_relation_filter_mapping(self):
        """Test that relation_exclusion_filter_mapping excludes related objects as expected."""
        book_1 = BookFactory(name='book 1')
        BookFactory(name='book 2')
        # Proofreaders for book 1 are not considered as referenced, and hence should appear in
        # the query results
        queryset = get_unreferenced_objects_query(
            Person,
            relation_exclusion_filter_mapping={
                Person._meta.get_field('proofread_books'): Q(name=book_1.name),
            },
        )

        assert list(queryset) == [book_1.proofreader]

    def test_only_excludes_referenced_objects(self):
        """Test that only referenced objects are excluded."""
        unreferenced_person = PersonFactory()
        BookFactory()
        queryset = get_unreferenced_objects_query(Person)
        assert list(queryset) == [unreferenced_person]
