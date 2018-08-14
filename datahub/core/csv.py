from codecs import BOM_UTF8
from csv import DictWriter

from django.http import FileResponse

from datahub.core.utils import EchoUTF8

CSV_CONTENT_TYPE = 'text/csv'
INCOMPLETE_CSV_MESSAGE = (
    '\r\n'
    'An error occurred while generating the CSV file. The file is incomplete.'
    '\r\n'
).encode('utf-8')


def csv_iterator(rows, field_titles):
    """Returns an iterator producing CSV formatted data from provided input."""
    try:
        yield BOM_UTF8
        writer = DictWriter(EchoUTF8(), fieldnames=field_titles.keys())

        yield writer.writerow(field_titles)
        for row in rows:
            yield writer.writerow(row)
    except Exception:
        # Because CSV responses are normally streamed, a 200 response will already have been
        # returned if an error occurs at this point. Hence we append an error to the CSV
        # contents (while re-raising the exception).
        yield INCOMPLETE_CSV_MESSAGE
        raise


def create_csv_response(rows, field_titles, filename):
    """Creates a CSV HTTP response."""
    # TODO: Use additional FileResponse.__init__() arguments when Django 2.1 is released
    # See https://code.djangoproject.com/ticket/16470
    response = FileResponse(
        csv_iterator(rows, field_titles),
        content_type=CSV_CONTENT_TYPE
    )

    filename = filename
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    return response
