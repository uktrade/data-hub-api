from datahub.documents.utils import get_bucket_name
from ..tasks import _get_report_key


def test_get_report_key():
    """Test that the report key is built from bucket name."""
    bucket_name = get_bucket_name('report')
    key = _get_report_key()

    assert bucket_name in key
