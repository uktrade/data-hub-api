from datetime import date
from random import shuffle

import pytest
from django.conf import settings
from django.db.models import F, Max
from django.db.models.functions import Left

from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_bracketed_concat_expression,
    get_choices_as_case_expression,
    get_front_end_url_expression,
    get_full_name_expression,
    get_string_agg_subquery,
    get_top_related_expression_subquery,
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
        author_names=get_string_agg_subquery(Book, 'authors__first_name'),
    )
    author_names_str = queryset.first().author_names
    actual_author_names = sorted(author_names_str.split(', ')) if author_names_str else []
    expected_author_names = sorted(author.first_name for author in authors)
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
            max_published=get_aggregate_subquery(Person, Max('proofread_books__published_on')),
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


@pytest.mark.parametrize('expression', ('name', F('name')))
def test_get_top_related_expression_subquery(expression):
    """
    Test that get_top_related_expression_subquery() can be used to get the name of the most
    recently published book.
    """
    person = PersonFactory()
    book_data = [
        {'name': 'oldest', 'published_on': date(2010, 1, 1)},
        {'name': 'in the middle', 'published_on': date(2013, 1, 1)},
        {'name': 'newest', 'published_on': date(2015, 1, 1)},
    ]
    shuffle(book_data)

    for item_data in book_data:
        BookFactory(
            proofreader=person,
            authors=[],
            **item_data,
        )

    queryset = Person.objects.annotate(
        name_of_latest_book=get_top_related_expression_subquery(
            Book.proofreader.field, expression, ('-published_on',),
        ),
    )
    assert queryset.first().name_of_latest_book == 'newest'


@pytest.mark.parametrize('genre', ('horror', 'non_fiction', 'invalid-option', None))
def test_get_choices_as_case_expression(genre):
    """
    Test that get_choices_as_case_expression() generates display names for a field with
    choices the same way that model_obj.get_FIELD_display() does.
    """
    book = BookFactory(genre=genre)
    queryset = Book.objects.annotate(
        genre_name=get_choices_as_case_expression(Book, 'genre'),
    )
    annotated_book = queryset.first()
    assert annotated_book.genre_name == book.get_genre_display()


class TestGetFullNameExpression:
    """Tests for get_full_name_expression()."""

    @pytest.mark.parametrize('include_country', (True, False))
    @pytest.mark.parametrize('country', ('French', '', None))
    def test_full_name_annotation(self, include_country, country):
        """Tests that a Person query set can be annotated with full names."""
        person = PersonFactory(country=country)
        bracketed_field_name = 'country' if include_country else None
        queryset = Person.objects.annotate(
            name=get_full_name_expression(bracketed_field_name=bracketed_field_name),
        )
        expected_name = f'{person.first_name} {person.last_name}'
        if country and include_country:
            expected_name += f' ({person.country})'

        assert queryset.first().name == expected_name

    def test_ignores_blank_first_name(self):
        """Tests that a blank first_name is ignored."""
        person = PersonFactory(first_name='')
        queryset = Person.objects.annotate(
            name=get_full_name_expression(),
        )
        assert queryset.first().name == person.last_name

    @pytest.mark.parametrize('include_country', (True, False))
    @pytest.mark.parametrize('country', ('French', '', None))
    def test_full_name_related_annotation(self, include_country, country):
        """
        Tests that a Book query set can be annotated with the full name of the proofreader
        of each book.
        """
        book = BookFactory(proofreader__country=country)
        proofreader = book.proofreader
        bracketed_field_name = 'country' if include_country else None
        queryset = Book.objects.annotate(
            proofreader_name=get_full_name_expression(
                person_field_name='proofreader',
                bracketed_field_name=bracketed_field_name,
            ),
        )
        expected_name = f'{proofreader.first_name} {proofreader.last_name}'
        if country and include_country:
            expected_name += f' ({proofreader.country})'
        assert queryset.first().proofreader_name == expected_name

    def test_none_for_none_relation(self):
        """Tests that None is returned for an unset foreign key."""
        BookFactory(proofreader=None)
        queryset = Book.objects.annotate(
            proofreader_name=get_full_name_expression('proofreader'),
        )
        assert queryset.first().proofreader_name is None


class TestBracketedConcatExpression:
    """Tests for get_bracketed_concat_expression()."""

    @pytest.mark.parametrize(
        'first_name,last_name,country,fields,bracketed_field,expected_value',
        (
            (
                'John',
                'Rogers',
                'France',
                ('first_name', 'last_name'),
                'country',
                'John Rogers (France)',
            ),
            (
                'John',
                'Sill',
                'France',
                ('last_name', 'first_name'),
                'country',
                'Sill John (France)',
            ),
            (
                'Alice',
                'Gentle',
                None,
                ('first_name', 'last_name'),
                'country',
                'Alice Gentle',
            ),
            (
                'Jennifer',
                '',
                'France',
                ('first_name', 'last_name'),
                None,
                'Jennifer',
            ),
            (
                'Carl',
                'Rogers',
                'UK',
                (),
                'country',
                '(UK)',
            ),
            (
                '',
                '',
                '',
                ('first_name', 'last_name'),
                'country',
                '',
            ),
        ),
    )
    def test_annotation(
        self,
        first_name,
        last_name,
        country,
        fields,
        bracketed_field,
        expected_value,
    ):
        """
        Tests that a Person query set can be annotated using get_bracketed_concat_expression().
        """
        PersonFactory(first_name=first_name, last_name=last_name, country=country)
        queryset = Person.objects.annotate(
            name=get_bracketed_concat_expression(
                *fields,
                expression_to_bracket=bracketed_field,
            ),
        )
        assert queryset.first().name == expected_value


def test_get_front_end_url_expression(monkeypatch):
    """Test that get_front_end_url_expression() generates URLs correctly."""
    monkeypatch.setitem(settings.DATAHUB_FRONTEND_URL_PREFIXES, 'book', 'http://test')

    book = BookFactory()
    queryset = Book.objects.annotate(
        url=get_front_end_url_expression('book', 'pk'),
    )
    assert queryset.first().url == f'http://test/{book.pk}'
