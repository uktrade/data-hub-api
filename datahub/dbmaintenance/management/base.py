import codecs
import csv
from contextlib import closing
from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.documents.utils import get_s3_client_for_bucket

logger = getLogger(__name__)


class CSVBaseCommand(BaseCommand):
    """
    Base class for db maintenance related commands.
    It helps dealing with processing rows in a CSV stored in S3,
    manages basic logging and failures.
    The operation is not atomic and each row is processed individually.

    Usage:
        class Command(CSVBaseCommand):
            def _process_row(self, row, **options):
                # process row['col1'], row['col2'] where col1, col2 are the
                # values in the header
                ...

        ./manage.py <command-name> <bucket> <object_key>
    """

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument('bucket', help='S3 bucket where the CSV is stored.')
        parser.add_argument('object_key', help='S3 key of the CSV file.')
        parser.add_argument(
            '--simulate',
            action='store_true',
            default=False,
            help='If True it only simulates the command without saving the changes.',
        )

    def _handle(self, *args, **options):
        """
        Internal version of the `handle` method.

        :returns: dict with count of records successful and failed updates
        """
        result = {True: 0, False: 0}

        s3_client = get_s3_client_for_bucket('default')
        response = s3_client.get_object(
            Bucket=options['bucket'],
            Key=options['object_key'],
        )['Body']

        with closing(response):
            csvfile = codecs.getreader('utf-8')(response)
            reader = csv.DictReader(csvfile)

            for row in reader:
                succeeded = self.process_row(row, **options)
                result[succeeded] += 1
        return result

    def handle(self, *args, **options):
        """Process the CSV file."""
        logger.info(f'Started')

        result = self._handle(*args, **options)

        logger.info(f'Finished - succeeded: {result[True]}, failed: {result[False]}')

    def process_row(self, row, **options):
        """
        Process one single row.

        :returns: True if the row has been processed successfully, False otherwise.
        """
        try:
            self._process_row(row, **options)
        except Exception as e:
            logger.exception(f'Row {row} - Failed')
            return False
        else:
            logger.info(f'Row {row} - OK')
            return True

    def _process_row(self, row, **options):
        """
        To be implemented by a subclass, it should propagate exceptions so that `process_row` knows
        that the row has not been successfully processed.

        :param row: dict where the keys are defined in the header and the values are the CSV row
        :param options: same as the django command options
        """
        raise NotImplementedError()
