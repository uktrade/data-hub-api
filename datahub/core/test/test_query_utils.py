from collections import Counter
from datetime import date
from random import sample, shuffle

import factory
import pytest
from django.conf import settings
from django.db.models import CharField, F, Max, Q, Value
from django.db.models.functions import Left

from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_array_agg_subquery,
    get_bracketed_concat_expression,
    get_choices_as_case_expression,
    get_empty_string_if_null_expression,
    get_front_end_url_expression,
    get_full_name_expression,
    get_queryset_object,
    get_string_agg_subquery,
    get_top_related_expression_subquery,
    JSONBBuildObject,
)
from datahub.core.test.support.factories import BookFactory, PersonFactory, PersonListItemFactory
from datahub.core.test.support.models import Book, Person, PersonListItem

pytestmark = pytest.mark.django_db


class TestJSONBBuildObject:
    """Tests for JSONBBuildObject."""

    def test_as_annotation(self):
        """Test that the function can be used as an annotation."""
        person = PersonFactory()
        queryset = Person.objects.annotate(
            data=JSONBBuildObject(first_name='first_name', last_name='last_name'),
        )
        assert queryset.first().data == {
            'first_name': person.first_name,
            'last_name': person.last_name,
        }


class TestGetStringAggSubquery:
    """Tests for get_string_agg_subquery()."""

    @pytest.mark.parametrize(
        'names,distinct,expected_result',
        (
            ([], False, None),
            (['Barbara'], False, 'Barbara'),
            (['Barbara', 'Claire'], False, 'Barbara, Claire'),
            (['Barbara', 'Claire', 'John'], False, 'Barbara, Claire, John'),
            (['Barbara', 'Claire', 'Claire'], False, 'Barbara, Claire, Claire'),
            ([], True, None),
            (['Barbara', 'Claire', 'John'], True, 'Barbara, Claire, John'),
            (['Barbara', 'Claire', 'Claire'], True, 'Barbara, Claire'),
            (
                ['Barbara', 'Barbara', 'Claire', 'John', 'John', 'John', 'Samantha'],
                True,
                'Barbara, Claire, John, Samantha',
            ),
        ),
    )
    def test_can_annotate_queryset(self, names, distinct, expected_result):
        """
        Test that the first names of all authors for each book can be concatenated into
        one field as a query set annotation for various cases.
        """
        authors = PersonFactory.create_batch(
            len(names),
            first_name=factory.Iterator(
                sample(names, len(names)),
            ),
        )
        BookFactory(authors=authors)
        queryset = Book.objects.annotate(
            author_names=get_string_agg_subquery(Book, 'authors__first_name', distinct=distinct),
        )
        actual_author_names = queryset.first().author_names
        assert actual_author_names == expected_result


class TestGetArrayAggSubquery:
    """Tests for get_array_agg_subquery()."""

    @pytest.mark.parametrize('distinct', (True, False))
    @pytest.mark.parametrize(
        'names',
        (
            [],
            ['Barbara'],
            ['Barbara', 'Claire'],
            ['Barbara', 'Claire', 'John'],
            ['Barbara', 'Claire', 'Claire'],
            ['Barbara', 'Barbara', 'Claire', 'John', 'John', 'John', 'Samantha'],
        ),
    )
    def test_aggregates_as_array(self, names, distinct):
        """
        Test that the first names of all authors for each book can be aggregated into an array
        for various cases, and with distinct on and off.
        """
        authors = PersonFactory.create_batch(
            len(names),
            first_name=factory.Iterator(
                sample(names, len(names)),
            ),
        )
        BookFactory(authors=authors)
        queryset = Book.objects.annotate(
            author_names=get_array_agg_subquery(
                Book.authors.through,
                'book',
                'person__first_name',
                distinct=distinct,
            ),
        )
        actual_author_names = queryset.first().author_names
        if distinct:
            assert Counter(actual_author_names) == Counter(set(names))
        else:
            assert Counter(actual_author_names) == Counter(names)

    @pytest.mark.parametrize(
        'names,desired_names', (
            (
                ['Barbara'], ['Barbara'],
            ),
            (
                ['Barbara', 'Claire'], ['Claire'],
            ),
            (
                ['Barbara', 'Claire', 'John', 'John'], ['Barbara', 'John'],
            ),
            (
                ['Barbara', 'Barbara', 'Claire', 'John', 'John', 'John', 'Samantha'],
                ['John', 'Samantha'],
            ),
        ),
    )
    def test_aggregates_as_filtered_array(self, names, desired_names):
        """
        Test that the desired first names of authors for each book can be aggregated into an array
        for various cases.
        """
        authors = PersonFactory.create_batch(
            len(names),
            first_name=factory.Iterator(
                sample(names, len(names)),
            ),
        )
        BookFactory(authors=authors)
        queryset = Book.objects.annotate(
            author_names=get_array_agg_subquery(
                Book.authors.through,
                'book',
                'person__first_name',
                filter=Q(person__first_name__in=desired_names),
            ),
        )
        actual_author_names = queryset.first()
        assert set(actual_author_names.author_names) == set(desired_names)

    @pytest.mark.parametrize(
        'ordering,expected_names',
        (
            ('person__first_name', ['Barbara', 'Claire', 'Samantha']),
            ('-person__first_name', ['Samantha', 'Claire', 'Barbara']),
        ),
    )
    def test_orders_results_when_ordering_specified(self, ordering, expected_names):
        """Test that the values are ordered corrected when an ordering is specified."""
        names = ['Barbara', 'Claire', 'Samantha']
        authors = PersonFactory.create_batch(
            len(names),
            first_name=factory.Iterator(
                sample(names, len(names)),
            ),
        )
        BookFactory(authors=authors)
        queryset = Book.objects.annotate(
            author_names=get_array_agg_subquery(
                Book.authors.through,
                'book',
                'person__first_name',
                ordering=ordering,
            ),
        )
        actual_author_names = queryset.first().author_names
        assert actual_author_names == expected_names


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


class TestGetTopRelatedExpressionSubquery:
    """Tests for get_top_related_expression_subquery()."""

    @pytest.mark.parametrize('expression', ('name', F('name')))
    def test_with_default_outer_field(self, expression):
        """
        Test that a Person query set can annotated with the name of the most
        recently published book.

        This considers a single many-to-one relationship between Book and Person.
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

    def test_with_custom_outer_field(self):
        """
        Test that a PersonListItem query set can be annotated with the name of the most
        recently published book for the person in the list item.

        This involves two relationships:

        - a many-to-one relationship between Book and Person
        - a many-to-one relationship between PersonListItem and Person

        A custom value is used for the outer_field argument.
        """
        person_list_item = PersonListItemFactory()
        book_data = [
            {'name': 'oldest', 'published_on': date(2010, 1, 1)},
            {'name': 'in the middle', 'published_on': date(2013, 1, 1)},
            {'name': 'newest', 'published_on': date(2015, 1, 1)},
        ]
        shuffle(book_data)

        for item_data in book_data:
            BookFactory(proofreader=person_list_item.person, authors=[], **item_data)

        queryset = PersonListItem.objects.annotate(
            name_of_latest_book=get_top_related_expression_subquery(
                Book.proofreader.field,
                'name',
                ('-published_on',),
                outer_field='person__pk',
            ),
        )
        assert queryset.first().name_of_latest_book == 'newest'

    def test_with_no_related_objects(self):
        """
        Test that, if a Person query set is annotated with the name of the most
        recently published proofread books, and there are no such books, the annotation
        value is None.

        This considers a single many-to-one relationship between Book and Person.
        """
        created_person = PersonFactory()

        queryset = Person.objects.annotate(
            name_of_latest_book=get_top_related_expression_subquery(
                Book.proofreader.field,
                'name',
                ('-published_on',),
            ),
        )
        returned_person = queryset.first()
        assert returned_person == created_person
        assert returned_person.name_of_latest_book is None


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


class TestGetQuerysetObject:
    """Tests for get_queryset_object()."""

    @pytest.mark.parametrize(
        'get_name,expected_exception',
        (
            (
                'Spring',
                Book.MultipleObjectsReturned,
            ),
            (
                'Winter',
                Book.DoesNotExist,
            ),
        ),
    )
    def test_raises_exception_when_not_one_match(self, get_name, expected_exception):
        """Test that exceptions are raised when no matches or multiple matches are found."""
        book_names = ['Spring', 'Spring', 'Summer']
        BookFactory.create_batch(
            len(book_names),
            name=factory.Iterator(book_names),
        )
        with pytest.raises(expected_exception):
            get_queryset_object(Book.objects.all(), name=get_name)

    def test_returns_object_when_one_match(self):
        """Test that the object is returned when there is exactly one match."""
        expected_book = BookFactory(name='Summer')
        BookFactory.create_batch(2, name='Spring')

        book = get_queryset_object(Book.objects.all(), name='Summer')
        assert book == expected_book


@pytest.mark.parametrize(
    'value,expected',
    (
        ('what', 'what'),
        (None, ''),
    ),
)
def test_get_empty_string_if_null_expression(value, expected):
    """Tests if None can be replaced with an empty string."""
    PersonFactory()
    query = Person.objects.annotate(
        possibly_null_value=Value(value, output_field=CharField(null=True)),
        some_property=get_empty_string_if_null_expression('possibly_null_value'),
    ).values('some_property')
    person = query.first()
    assert person['some_property'] == expected
