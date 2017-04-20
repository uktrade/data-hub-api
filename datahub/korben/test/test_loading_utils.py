from collections import namedtuple
from datetime import datetime, timezone
from unittest import mock

from datahub.korben import utils


def test_cdms_datetime_to_datetime():
    """Test valid date."""
    cdms_date_str = '/Date(1491223812000)/'
    assert utils.cdms_datetime_to_datetime(cdms_date_str) == datetime(2017, 4, 3, 12, 50, 12, tzinfo=timezone.utc)


def test_cdms_datetime_to_datetime_does_not_overwrite_dates():
    """Test retuning date."""
    value = datetime.utcnow()
    assert utils.cdms_datetime_to_datetime(value) is value


def test_cdms_datetime_to_datetime_returns_none_on_error():
    """Test silent ignore."""
    assert utils.cdms_datetime_to_datetime('invalid') is None


@mock.patch('loading_scripts.utils.get_cdms_entity_s3_keys')
@mock.patch('loading_scripts.utils.load_json_from_s3_bucket')
def test_iterate_over_cdms_entities(import_mock, keys_mock):
    """Test combined iteration."""
    keys_mock.return_value = ['location1', 'location2']
    import_mock.return_value = dict(d=dict(results=[1]))

    assert list(utils.iterate_over_cdms_entities_from_s3(None, 'irrelevant')) == [1, 1]


def test_cdms_keys_filtering():
    """Test filtering of S3 objects."""
    s3_result = namedtuple('s3_result', ['key'])
    bucket = mock.Mock()
    bucket.objects.filter.return_value = [
        s3_result('test/request_body'),
        s3_result('test/response_body'),
    ]

    assert utils.get_cdms_entity_s3_keys(bucket, 'test') == ['test/response_body']
