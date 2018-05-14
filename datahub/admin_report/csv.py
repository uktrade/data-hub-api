from codecs import BOM_UTF8
from csv import DictWriter

from datahub.core.utils import EchoUTF8


def csv_iterator(rows, field_titles):
    """Returns an iterator producing CSV formatted data from provided input."""
    yield BOM_UTF8
    writer = DictWriter(EchoUTF8(), fieldnames=field_titles.keys())

    yield writer.writerow(field_titles)
    for row in rows:
        yield writer.writerow(row)
