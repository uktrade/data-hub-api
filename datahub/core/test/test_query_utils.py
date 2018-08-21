import pytest
from django.conf import settings
from django.db.models import Max
from django.db.models.functions import Left

from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_choices_as_case_expression,
    get_front_end_url_expression,
    get_full_name_expression,
    get_string_agg_subquery,
)
from datahub.core.test.support.factories import BookFactory, PersonFactory
from datahub.core.test.support.models import Book, Person


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('num_authors', range(3))
def test_get_string_agg_subquery(num_authors):
    """
    Test that get_string_agg_subquery() can be used to concatenate the first names of
    all authors for each book into one field.
    """
    authors = PersonFactory.create_batch(num_authors)
    BookFactory(authors=authors)
    queryset = Book.objects.annotate(
        author_names=get_string_agg_subquery(Book, 'authors__first_name')
    )
    author_names_str = queryset.first().author_names
    actual_author_names = author_names_str.split(', ') if author_names_str else []
    expected_author_names = [author.first_name for author in authors]
    assert actual_author_names == expected_author_names


class TestGetAggregateSubquery:
    """Tests for get_aggregate_subquery()."""

    @pytest.mark.parametrize('num_books', (0, 5))
    def test_with_max_aggregate_expression(self, num_books):
        """
        Test that Max() can be used to calculate the maximum published-on date for the books a
        person has proofread.
        """
        proofreader = PersonFactory()
        books = BookFactory.create_batch(num_books, proofreader=proofreader)
        queryset = Person.objects.annotate(
            max_published=get_aggregate_subquery(Person, Max('proofread_books__published_on'))
        ).filter(
            pk=proofreader.pk,
        )
        actual_max_published = queryset.first().max_published
        expected_max_published = max(book.published_on for book in books) if num_books else None
        assert actual_max_published == expected_max_published

    def test_get_aggregate_subquery_raises_error_on_on_aggregate_expression(self):
        """
        Test that an error is raised when passed a non-aggregate expression.
        """
        with pytest.raises(ValueError):
            get_aggregate_subquery(Person, Left('proofread_books__name', 5))


@pytest.mark.parametrize('genre', ('horror', 'non_fiction', 'invalid-option', None))
def test_get_choices_as_case_expression(genre):
    """
    Test that get_choices_as_case_expression() generates display names for a field with
    choices the same way that model_obj.get_FIELD_display() does.
    """
    book = BookFactory(genre=genre)
    queryset = Book.objects.annotate(
        genre_name=get_choices_as_case_expression(Book, 'genre')
    )
    annotated_book = queryset.first()
    assert annotated_book.genre_name == book.get_genre_display()


class TestGetFullNameExpression:
    """Tests for get_full_name_expression()."""

    def test_full_name_annotation(self):
        """
        Tests that a Book query set can be annotated with the full name of the proofreader
        of each book.
        """
        book = BookFactory()
        proofreader = book.proofreader
        queryset = Book.objects.annotate(
            proofreader_name=get_full_name_expression('proofreader')
        )
        expected_name = f'{proofreader.first_name} {proofreader.last_name}'
        assert queryset.first().proofreader_name == expected_name

    def test_none_for_none_relation(self):
        """Tests that None is returned for an unset foreign key."""
        BookFactory(proofreader=None)
        queryset = Book.objects.annotate(
            proofreader_name=get_full_name_expression('proofreader')
        )
        assert queryset.first().proofreader_name is None


def test_get_front_end_url_expression(monkeypatch):
    """Test that get_front_end_url_expression() generates URLs correctly."""
    monkeypatch.setitem(settings.DATAHUB_FRONTEND_URL_PREFIXES, 'book', 'http://test')

    book = BookFactory()
    queryset = Book.objects.annotate(
        url=get_front_end_url_expression('book', 'pk')
    )
    assert queryset.first().url == f'http://test/{book.pk}'
