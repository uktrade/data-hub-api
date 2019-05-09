import csv
import io

from datahub.core.test_utils import random_obj_for_queryset
from datahub.interaction.models import CommunicationChannel
from datahub.metadata.models import Service


def random_communication_channel(disabled=False):
    """Get a random communication channel."""
    return random_obj_for_queryset(
        CommunicationChannel.objects.filter(disabled_on__isnull=not disabled),
    )


def random_service(disabled=False):
    """Get a random service."""
    return random_obj_for_queryset(
        Service.objects.filter(disabled_on__isnull=not disabled),
    )


def make_csv_file(*rows, encoding='utf-8-sig', filename='test.csv'):
    """Make a CSV file from a number of sequences."""
    with io.StringIO() as text_stream:
        writer = csv.writer(text_stream)
        writer.writerows(rows)

        data = text_stream.getvalue().encode(encoding)

    stream = io.BytesIO(data)
    stream.name = filename
    return stream
