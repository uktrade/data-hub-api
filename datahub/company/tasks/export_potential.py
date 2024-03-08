import logging

from django.core.management import call_command

logger = logging.getLogger(__name__)


def update_company_export_potential_from_csv(bucket, object_key, simulate=False):
    """
    Call the management command to update company export potential from a CSV file stored in S3.

    :param bucket: Name of the S3 bucket where the CSV is stored.
    :param object_key: S3 object key (path to the CSV file within the bucket).
    :param simulate: If True, run the command in simulate mode without changing the database.
    """
    call_command(
        'update_company_export_potential_date',
        bucket=bucket,
        object_key=object_key,
        simulate=simulate,
    )
