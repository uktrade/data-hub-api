from datetime import date
from enum import Enum
from unittest import mock
from uuid import UUID

import pytest

from datahub.core.constants import Constant
from datahub.core.test.support.models import MetadataModel
from datahub.core.utils import (
    force_uuid,
    get_financial_year,
    join_truthy_strings,
    load_constants_to_database,
    log_to_sentry,
    reverse_with_query_string,
    slice_iterable_into_chunks,
)


class TestForceUUID:
    """Tests for force_uuid()."""

    @pytest.mark.parametrize(
        'value,expected_result',
        (
            (None, None),
            ('b3eb3eb2-9b83-4253-b77c-f3eca5a6a660', UUID('b3eb3eb2-9b83-4253-b77c-f3eca5a6a660')),
            (
                UUID('b3eb3eb2-9b83-4253-b77c-f3eca5a6a660'),
                UUID('b3eb3eb2-9b83-4253-b77c-f3eca5a6a660'),
            ),
        ),
    )
    def test_converts_values(self, value, expected_result):
        """Test that values are converted to UUIDs as necessary."""
        assert force_uuid(value) == expected_result

    @pytest.mark.parametrize('value', (b'', []))
    def test_raises_error_on_unexpected_type(self, value):
        """Test that an error is raised on unexpected types."""
        with pytest.raises(TypeError):
            force_uuid(value)


@pytest.mark.parametrize(
    'args,sep,res',
    (
        (('abc', 'def', 'ghi'), ',', 'abc,def,ghi'),
        (('abc', 'def'), ' ', 'abc def'),
        (('abc', ''), ' ', 'abc'),
        (('abc', None), ' ', 'abc'),
        ((None, ''), ' ', ''),
        ((), ' ', ''),
    ),
)
def test_join_truthy_strings(args, sep, res):
    """Tests joining turthy strings."""
    assert join_truthy_strings(*args, sep=sep) == res


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
    """
    Test loading constants to the database.

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
    'query_args,expected_url',
    (
        ({}, '/test-disableable/?'),
        ({'123': 'abc'}, '/test-disableable/?123=abc'),
        ({'ab': ['1', '2']}, '/test-disableable/?ab=1&ab=2'),
    ),
)
@pytest.mark.urls('datahub.core.test.support.urls')
def test_reverse_with_query_string(query_args, expected_url):
    """Test reverse_with_query_string() for various query arguments."""
    assert reverse_with_query_string('test-disableable-collection', query_args) == expected_url


@pytest.mark.parametrize(
    'date_obj,expected_financial_year',
    (
        (None, None),
        (date(1980, 1, 1), 1979),
        (date(2018, 1, 1), 2017),
        (date(2019, 3, 1), 2018),
        (date(2019, 8, 1), 2019),
        (date(2025, 3, 1), 2024),
        (date(2025, 4, 1), 2025),
        (date(2025, 3, 31), 2024),
    ),
)
def test_get_financial_year(date_obj, expected_financial_year):
    """Test for get financial year"""
    assert get_financial_year(date_obj) == expected_financial_year


@pytest.mark.parametrize(
    'extra',
    (
        None,
        {'bar': 'baz', 'a': 'b'},
    ),
)
@pytest.mark.parametrize(
    'level',
    (
        None,
        'warning',
    ),
)
@mock.patch('datahub.core.utils.sentry_sdk.push_scope')
@mock.patch('datahub.core.utils.sentry_sdk.capture_message')
def test_log_to_sentry(mocked_capture_message, mocked_push_scope, level, extra):
    """
    Test log_to_sentry utility.
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
