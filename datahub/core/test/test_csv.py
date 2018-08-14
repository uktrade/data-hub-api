import pytest

from datahub.core.csv import csv_iterator, INCOMPLETE_CSV_MESSAGE


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
        for row in csv_iterator(_rows(), {'id': 'id'}):
            pass

    assert row == INCOMPLETE_CSV_MESSAGE
