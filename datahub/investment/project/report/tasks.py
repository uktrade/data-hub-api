import logging
import tempfile

from django.utils.timezone import now

from datahub.core.queues.constants import EVERY_EIGHT_AM
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.documents.utils import get_bucket_name, get_s3_client_for_bucket
from datahub.investment.project.report.models import SPIReport
from datahub.investment.project.report.spi import write_report

logger = logging.getLogger(__name__)


def _get_report_key():
    report_id = now().strftime('%Y-%m-%d %H%M%S')
    key = f'spi-reports/SPI Report {report_id}.csv'
    return key


# Generated SPI Reports are no longer used. Conversion from Celery to RQ has not been tested.
def schedule_generate_spi_report():
    job = job_scheduler(
        function='generate_spi_report',
        cron=EVERY_EIGHT_AM,
    )
    logger.info(
        f'Task {job.id} schedule_generate_spi_report',
    )
    return job


def generate_spi_report():
    """Schedule RQ task that generates SPI report."""
    with tempfile.TemporaryFile(mode='wb+') as file:
        write_report(file)

        file.seek(0)

        report_key = _get_report_key()
        s3_client = get_s3_client_for_bucket('report')
        s3_client.upload_fileobj(
            file,
            get_bucket_name('report'),
            report_key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',
            },
        )

        report = SPIReport(
            s3_key=report_key,
        )
        report.save()

    logger.info(
        'Task generate_spi_report completed',
    )
