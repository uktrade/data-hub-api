from freezegun import freeze_time

from datahub.investment.project.report.tasks import _get_report_key


@freeze_time('2018-03-01 01:02:03')
def test_get_report_key():
    """Test that the report key is built from current date and time."""
    key = _get_report_key()
    assert key == 'spi-reports/SPI Report 2018-03-01 010203.csv'
