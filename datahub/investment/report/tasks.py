import tempfile

from celery.task import task
from django.conf import settings
from django.utils.timezone import now

from datahub.investment.report.models import SPIReport
from datahub.investment.report.utils import get_report_s3_client
from .spi import write_report


def _get_report_key():
    report_id = now().strftime('%Y-%m-%d %H%M%S')
    key = f'{settings.REPORT_BUCKET}/spi-reports/SPI Report {report_id}.csv'
    return key


@task(ignore_result=True)
def generate_spi_report():
    """Celery task that generates SPI report."""
    with tempfile.TemporaryFile(mode='wb+') as file:
        write_report(file)

        file.seek(0)

        report_key = _get_report_key()
        s3_client = get_report_s3_client()
        s3_client.upload_fileobj(
            file,
            settings.REPORT_BUCKET,
            report_key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256'
            }
        )

        report = SPIReport(
            s3_key=report_key
        )
        report.save()
