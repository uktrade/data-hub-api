import tempfile

from celery.task import task
from django.utils.timezone import now

from datahub.documents.utils import get_bucket_name, get_s3_client_for_bucket
from datahub.investment.project.report.models import SPIReport
from datahub.investment.project.report.spi import write_report


def _get_report_key():
    report_id = now().strftime('%Y-%m-%d %H%M%S')
    key = f'spi-reports/SPI Report {report_id}.csv'
    return key


@task(acks_late=True)
def generate_spi_report():
    """Celery task that generates SPI report."""
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
