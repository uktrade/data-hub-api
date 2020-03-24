from codecs import BOM_UTF8
from csv import DictWriter
from datetime import datetime
from decimal import Decimal
from itertools import chain

from django.http import StreamingHttpResponse

from datahub.core.utils import EchoUTF8

CSV_CONTENT_TYPE = 'text/csv; charset=utf-8'
INCOMPLETE_CSV_MESSAGE = (
    '\r\n'
    'An error occurred while generating the CSV file. The file is incomplete.'
    '\r\n'
).encode('utf-8')


def _flatten(list_of_lists):
    """Flatten one level of nesting"""
    return chain.from_iterable(list_of_lists)


def _default_page_transformer_func(data):
    """
    Default no-op hook for page transformation.
    """
    return data


def _csv_list_iterator(
        rows,
        field_titles,
        page_size=None,
        page_transformer_func=None,
):
    """
    Returns an iterator producing a list containing one or more rows on each
    yield from provided input.

    This allows paging through underlying rows and applying a bulk transformation
    function if required.
    """
    if not page_transformer_func:
        page_transformer_func = _default_page_transformer_func

    try:
        yield [BOM_UTF8]
        writer = DictWriter(EchoUTF8(), fieldnames=field_titles.keys())
        yield [writer.writerow(field_titles)]
        page = []
        for row in rows:
            page.append(_transform_csv_row(row))
            if len(page) == page_size or not page_size:
                yield [writer.writerow(x) for x in page_transformer_func(page)]
                page = []
        yield [writer.writerow(x) for x in page_transformer_func(page)]
    except Exception:
        # Because CSV responses are normally streamed, a 200 response will already have been
        # returned if an error occurs at this point. Hence we append an error to the CSV
        # contents (while re-raising the exception).
        yield [INCOMPLETE_CSV_MESSAGE]
        raise


def csv_iterator(
        rows,
        field_titles,
        page_size=None,
        page_transformer_func=None,
):
    """Returns an iterator producing CSV formatted data from provided input."""
    for line in _flatten(_csv_list_iterator(
            rows,
            field_titles,
            page_size,
            page_transformer_func,
    )):
        yield line


def create_csv_response(
        rows,
        field_titles,
        filename,
        streaming_page_size=None,
        page_transformer_func=None,
):
    """Creates a CSV HTTP response."""
    # Note: FileResponse is not used as it is designed for file-like objects, while we are using
    # a generator here.
    response = StreamingHttpResponse(
        csv_iterator(rows, field_titles, page_size=streaming_page_size,
                     page_transformer_func=page_transformer_func),
        content_type=CSV_CONTENT_TYPE,
    )

    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    return response


def _transform_csv_row(row):
    return {key: _transform_csv_value(val) for key, val in row.items()}


def _transform_csv_value(value):
    """
    Transforms values before they are written to a CSV file for better compatibility with Excel.

    In particular, datetimes are formatted in a way that results in better compatibility with
    Excel. Other values are passed through unchanged (the csv module automatically formats None
    as an empty string).

    These transformations are specific to CSV files and won't necessarily apply to other file
    formats.
    """
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, Decimal):
        normalized_value = value.normalize()
        return f'{normalized_value:f}'
    return value
