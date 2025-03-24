from datetime import date
from enum import Enum
from unittest import mock
from uuid import UUID

import pytest

from datahub.core.constants import Constant
from datahub.core.test.support.models import MetadataModel
from datahub.core.utils import (
    force_uuid,
    format_currency,
    format_currency_range,
    format_currency_range_string,
    get_financial_year,
    join_truthy_strings,
    load_constants_to_database,
    log_to_sentry,
    reverse_with_query_string,
    slice_iterable_into_chunks,
    upper_snake_case_to_sentence_case,
)


class TestForceUUID:
    """Tests for force_uuid()."""

    @pytest.mark.parametrize(
        ('value', 'expected_result'),
        [
            (None, None),
            ('b3eb3eb2-9b83-4253-b77c-f3eca5a6a660', UUID('b3eb3eb2-9b83-4253-b77c-f3eca5a6a660')),
            (
                UUID('b3eb3eb2-9b83-4253-b77c-f3eca5a6a660'),
                UUID('b3eb3eb2-9b83-4253-b77c-f3eca5a6a660'),
            ),
        ],
    )
    def test_converts_values(self, value, expected_result):
        """Test that values are converted to UUIDs as necessary."""
        assert force_uuid(value) == expected_result

    @pytest.mark.parametrize('value', [b'', []])
    def test_raises_error_on_unexpected_type(self, value):
        """Test that an error is raised on unexpected types."""
        with pytest.raises(TypeError):
            force_uuid(value)


@pytest.mark.parametrize(
    ('args', 'sep', 'res'),
    [
        (('abc', 'def', 'ghi'), ',', 'abc,def,ghi'),
        (('abc', 'def'), ' ', 'abc def'),
        (('abc', ''), ' ', 'abc'),
        (('abc', None), ' ', 'abc'),
        ((None, ''), ' ', ''),
        ((), ' ', ''),
    ],
)
def test_join_truthy_strings(args, sep, res):
    """Tests joining turthy strings."""
    assert join_truthy_strings(*args, sep=sep) == res


@pytest.mark.parametrize(
    ('string', 'glue', 'expected'),
    [
        ('UPPER_SNAKE_CASE', '+', 'Upper snake case'),
        (['UPPER_SNAKE_CASE', 'LINE_2'], '+', 'Upper snake case+Line 2'),
        (['UPPER_SNAKE_CASE', 'LINE_2'], '\n', 'Upper snake case\nLine 2'),
        (['UPPER_SNAKE_CASE', 'LINE_2'], '. ', 'Upper snake case. Line 2'),
    ],
)
def test_upper_snake_case_to_sentence_case(string, glue, expected):
    """Test formatting currency."""
    assert upper_snake_case_to_sentence_case(string, glue) == expected


@pytest.mark.parametrize(
    ('string', 'expected'),
    [
        ('UPPER_SNAKE_CASE', 'Upper snake case'),
        (['UPPER_SNAKE_CASE', 'LINE_2'], 'Upper snake case Line 2'),
    ],
)
def test_default_glue_upper_snake_case_to_sentence_case(string, expected):
    """Test formatting currency."""
    assert upper_snake_case_to_sentence_case(string) == expected


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (0, '£0'),
        (1, '£1'),
        (1.5, '£1.50'),
        (999999, '£999,999'),
        (1000000, '£1 million'),
        (1234567, '£1.23 million'),
        (7000000, '£7 million'),
        (999990000, '£999.99 million'),
        (999999999, '£1 billion'),
        (1000000000, '£1 billion'),
        (1200000000, '£1.2 billion'),
        (1234567890, '£1.23 billion'),
        (7000000000, '£7 billion'),
        (123000000000, '£123 billion'),
        (1234000000000, '£1,234 billion'),
        (1234500000000, '£1,234.5 billion'),
    ],
)
def test_format_currency(value, expected):
    """Test formatting currency."""
    assert format_currency(str(value)) == expected
    assert format_currency(value) == expected

    # Test without currency symbols
    assert format_currency(str(value), symbol='') == expected.replace('£', '')
    assert format_currency(value, symbol='') == expected.replace('£', '')

    # Test with different currency symbols
    assert format_currency(str(value), symbol='A$') == expected.replace('£', 'A$')
    assert format_currency(value, symbol='A$') == expected.replace('£', 'A$')


@pytest.mark.parametrize(
    ('values', 'expected'),
    [
        ([0, 1.5], '£0 to £1.50'),
        ([999999, 1000000], '£999,999 to £1 million'),
        ([1234567, 7000000], '£1.23 million to £7 million'),
        ([999990000, 999999999], '£999.99 million to £1 billion'),
        ([1200000000, 0.01], '£1.2 billion to £0.01'),
    ],
)
def test_format_currency_range(values, expected):
    assert format_currency_range(values) == expected
    assert format_currency_range(values, symbol='') == expected.replace('£', '')
    assert format_currency_range(values, symbol='A$') == expected.replace('£', 'A$')


@pytest.mark.parametrize(
    ('string', 'expected'),
    [
        ('0-9999', 'Less than £10,000'),
        ('0-10000', 'Less than £10,000'),
        ('0-1000000', 'Less than £1 million'),
        ('10000-500000', '£10,000 to £500,000'),
        ('500001-1000000', '£500,001 to £1 million'),
        ('1000001-2000000', '£1 million to £2 million'),
        ('2000001-5000000', '£2 million to £5 million'),
        ('5000001-10000000', '£5 million to £10 million'),
        ('10000001+', 'More than £10 million'),
        ('SPECIFIC_AMOUNT', 'Specific amount'),
    ],
)
def test_format_currency_range_string(string, expected):
    """Test range with and without currency symbol.
    """
    assert format_currency_range_string(string) == expected
    assert format_currency_range_string(string, symbol='') == expected.replace('£', '')
    assert format_currency_range_string(string, symbol='A$') == expected.replace('£', 'A$')


@pytest.mark.parametrize(
    ('string', 'expected'),
    [
        ('0...9999', 'Less than £10,000'),
        ('0...10000', 'Less than £10,000'),
        ('0...1000000', 'Less than £1 million'),
        ('10000...500000', '£10,000 to £500,000'),
        ('500001...1000000', '£500,001 to £1 million'),
        ('1000001...2000000', '£1 million to £2 million'),
        ('2000001...5000000', '£2 million to £5 million'),
        ('5000001...10000000', '£5 million to £10 million'),
        ('10000001+', 'More than £10 million'),
        ('SPECIFIC_AMOUNT', 'Specific amount'),
    ],
)
def test_format_currency_range_string_separator(string, expected):
    """Test range with separator symbol.
    """
    assert format_currency_range_string(string, separator='...') == expected


@pytest.mark.parametrize(
    ('string', 'more_or_less', 'smart_more_or_less', 'expected'),
    [
        ('', True, True, ''),
        ('0-9999', True, True, 'Less than £10,000'),
        ('0-10000', True, True, 'Less than £10,000'),
        ('0-1000000', True, True, 'Less than £1 million'),
        ('10000001+', True, True, 'More than £10 million'),
        ('SPECIFIC_AMOUNT', True, True, 'Specific amount'),
        ('0-9999', True, False, 'Less than £9,999'),
        ('0-10000', True, False, 'Less than £10,000'),
        ('0-1000000', True, False, 'Less than £1 million'),
        ('10000001+', True, False, 'More than £10 million'),
        ('SPECIFIC_AMOUNT', True, False, 'Specific amount'),
        # smart_more_or_less is not used when more_or_less is False.
        ('0-9999', False, False, '£0 to £9,999'),
        ('0-10000', False, False, '£0 to £10,000'),
        ('0-1000000', False, False, '£0 to £1 million'),
        ('10000001+', False, False, '£10 million+'),
        ('', False, False, ''),
        # Return string as Sentence case for invalid numbers
        ('SPECIFIC_AMOUNT', False, False, 'Specific amount'),
    ],
)
def test_format_currency_range_string_more_or_less_parameters(
        string,
        more_or_less,
        smart_more_or_less,
        expected,
):
    """Test range with and without currency symbol.
    """
    assert format_currency_range_string(
        string, more_or_less=more_or_less, smart_more_or_less=smart_more_or_less) == expected
    assert format_currency_range_string(
        string, more_or_less=more_or_less, smart_more_or_less=smart_more_or_less, symbol='') == \
        expected.replace('£', '')
    assert format_currency_range_string(
        string, more_or_less=more_or_less, smart_more_or_less=smart_more_or_less, symbol='A$') == \
        expected.replace('£', 'A$')


def test_slice_iterable_into_chunks():
    """Test slice iterable into chunks."""
    size = 2
    iterable = range(5)
    chunks = list(slice_iterable_into_chunks(iterable, size))
    assert chunks == [[0, 1], [2, 3], [4]]


class _MetadataModelConstant(Enum):
    object_2 = Constant('Object 2a', 'c2ed6ff6-4a09-41ba-bda2-f4cdb2f96833')
    object_3 = Constant('Object 3b', '09afd6ef-deff-4b0f-9c5b-4816d3ddac09')
    object_4 = Constant('Object 4', 'c8ecf162-f14a-4ab2-a570-fb70a2435e6b')
    object_5 = Constant('Object 5', '6ea0e2a2-0b2b-408c-a621-aff49f58496e')


@pytest.mark.django_db
def test_load_constants_to_database():
    """Test loading constants to the database.

    Makes sure that new values are created, existing ones are updated and none are deleted.
    """
    initial_objects = [
        {
            'id': 'e2b77f5f-a3d9-4c48-9d40-5a5427ddcfc2',
            'name': 'Object 1',
        },
        {
            'id': 'c2ed6ff6-4a09-41ba-bda2-f4cdb2f96833',
            'name': 'Object 2',
        },
        {
            'id': '09afd6ef-deff-4b0f-9c5b-4816d3ddac09',
            'name': 'Object 3',
        },
        {
            'id': 'c8ecf162-f14a-4ab2-a570-fb70a2435e6b',
            'name': 'Object 4',
        },
    ]

    MetadataModel.objects.bulk_create([MetadataModel(**data) for data in initial_objects])

    load_constants_to_database(_MetadataModelConstant, MetadataModel)

    expected_items = {
        (UUID('e2b77f5f-a3d9-4c48-9d40-5a5427ddcfc2'), 'Object 1'),  # not deleted
        (UUID('c2ed6ff6-4a09-41ba-bda2-f4cdb2f96833'), 'Object 2a'),  # name updated
        (UUID('09afd6ef-deff-4b0f-9c5b-4816d3ddac09'), 'Object 3b'),  # name updated
        (UUID('c8ecf162-f14a-4ab2-a570-fb70a2435e6b'), 'Object 4'),  # unchanged
        (UUID('6ea0e2a2-0b2b-408c-a621-aff49f58496e'), 'Object 5'),  # created
    }
    actual_items = {(obj.id, obj.name) for obj in MetadataModel.objects.all()}
    assert actual_items == expected_items


@pytest.mark.parametrize(
    ('query_args', 'expected_url'),
    [
        ({}, '/test-disableable/?'),
        ({'123': 'abc'}, '/test-disableable/?123=abc'),
        ({'ab': ['1', '2']}, '/test-disableable/?ab=1&ab=2'),
    ],
)
@pytest.mark.urls('datahub.core.test.support.urls')
def test_reverse_with_query_string(query_args, expected_url):
    """Test reverse_with_query_string() for various query arguments."""
    assert reverse_with_query_string('test-disableable-collection', query_args) == expected_url


@pytest.mark.parametrize(
    ('date_obj', 'expected_financial_year'),
    [
        (None, None),
        (date(1980, 1, 1), 1979),
        (date(2018, 1, 1), 2017),
        (date(2019, 3, 1), 2018),
        (date(2019, 8, 1), 2019),
        (date(2025, 3, 1), 2024),
        (date(2025, 4, 1), 2025),
        (date(2025, 3, 31), 2024),
    ],
)
def test_get_financial_year(date_obj, expected_financial_year):
    """Test for get financial year."""
    assert get_financial_year(date_obj) == expected_financial_year


@pytest.mark.parametrize(
    'extra',
    [
        None,
        {'bar': 'baz', 'a': 'b'},
    ],
)
@pytest.mark.parametrize(
    'level',
    [
        None,
        'warning',
    ],
)
@mock.patch('datahub.core.utils.sentry_sdk.push_scope')
@mock.patch('datahub.core.utils.sentry_sdk.capture_message')
def test_log_to_sentry(mocked_capture_message, mocked_push_scope, level, extra):
    """Test log_to_sentry utility.
    """
    kwargs = {}
    expected_extra = {}
    if extra:
        kwargs['extra'] = extra
        expected_extra = extra
    expected_level = 'info'
    if level:
        kwargs['level'] = level
        expected_level = level

    log_to_sentry('foo', **kwargs)

    mocked_capture_message.assert_called_with('foo', level=expected_level)
    mocked_scope = mocked_push_scope.return_value.__enter__.return_value
    for key, value in expected_extra.items():
        mocked_scope.set_extra.assert_any_call(key, value)
