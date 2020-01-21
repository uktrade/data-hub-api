import csv
import io
from functools import reduce
from operator import or_

import factory

from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.core.test_utils import random_obj_for_queryset
from datahub.interaction.models import CommunicationChannel, Interaction
from datahub.interaction.test.utils import random_service


def random_communication_channel(disabled=False):
    """Get a random communication channel."""
    return random_obj_for_queryset(
        CommunicationChannel.objects.filter(disabled_on__isnull=not disabled),
    )


def make_csv_file(fieldnames, *rows, encoding='utf-8-sig', filename='test.csv'):
    """Make a CSV file from a number of sequences."""
    row_dicts = [
        {field_name: field_value for field_name, field_value in zip(fieldnames, row)}
        for row in rows
    ]

    return make_csv_file_from_dicts(
        *row_dicts,
        fieldnames=fieldnames,
        encoding=encoding,
        filename=filename,
    )


def make_csv_file_from_dicts(*rows, fieldnames=None, encoding='utf-8-sig', filename='test.csv'):
    """Make a CSV file from a number of dicts."""
    if fieldnames is None:
        fieldnames = reduce(or_, (row.keys() for row in rows))

    with io.StringIO() as text_stream:
        writer = csv.DictWriter(text_stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        data = text_stream.getvalue().encode(encoding)

    stream = io.BytesIO(data)
    stream.name = filename
    return stream


def make_matched_rows(num_records):
    """Make multiple interaction CSV rows that should pass contact matching."""
    adviser = AdviserFactory(
        first_name='Adviser for',
        last_name='Matched interaction',
    )
    service = random_service()
    communication_channel = random_communication_channel()
    contacts = ContactFactory.create_batch(
        num_records,
        email=factory.Sequence(lambda i: f'unique{i}@matched.uk'),
    )

    return [
        {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.Kind.INTERACTION,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
            'service': service.name,
            'communication_channel': communication_channel.name,
        }
        for contact in contacts
    ]


def make_multiple_matches_rows(num_records):
    """Make multiple interaction CSV rows that should have multiple contact matches."""
    adviser = AdviserFactory(
        first_name='Adviser for',
        last_name='Multi-matched interaction',
    )
    service = random_service()
    communication_channel = random_communication_channel()

    contact_email = 'duplicate@duplicate.uk'
    ContactFactory.create_batch(2, email=contact_email)

    return [
        {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.Kind.INTERACTION,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': contact_email,
            'service': service.name,
            'communication_channel': communication_channel.name,
        }
        for _ in range(num_records)
    ]


def make_unmatched_rows(num_records):
    """Make multiple interaction CSV rows that should have no contact matches."""
    adviser = AdviserFactory(
        first_name='Adviser for',
        last_name='Unmatched interaction',
    )
    service = random_service()
    communication_channel = random_communication_channel()

    return [
        {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.Kind.INTERACTION,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': f'unmatched{i}@unmatched.uk',
            'service': service.name,
            'communication_channel': communication_channel.name,
        }
        for i in range(num_records)
    ]
