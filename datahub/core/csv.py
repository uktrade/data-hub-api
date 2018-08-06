from codecs import BOM_UTF8
from csv import DictWriter

from django.http import FileResponse

from datahub.core.utils import EchoUTF8

CSV_CONTENT_TYPE = 'text/csv'


def csv_iterator(rows, field_titles):
    """Returns an iterator producing CSV formatted data from provided input."""
    yield BOM_UTF8
    writer = DictWriter(EchoUTF8(), fieldnames=field_titles.keys())

    yield writer.writerow(field_titles)
    for row in rows:
        yield writer.writerow(row)


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
